import sys, random

from PySide2.QtWidgets import QWidget, QApplication, QScrollArea, QVBoxLayout, QSizePolicy, QHBoxLayout, QLabel, QFrame
from PySide2.QtCore import QPoint, QEvent, Qt, QRect, QObject, Signal
from PySide2.QtGui import QPaintEvent, QPainter, QBrush, QColor, QPen, QWheelEvent, QMouseEvent


from panels.ui_panel01 import Ui_Panel01

class PanelHeader(QLabel):

    clicked = Signal()

    def __init__(self, label:str, parent=None):
        super().__init__(label, parent=parent)
        self.setText(label)

        self.setFixedHeight(30)
        self.setContentsMargins(10,0,10,0)

        self._is_pressed = False
        self._pressed_pos:QPoint = QPoint()

    def mousePressEvent(self, event:QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._pressed_pos = event.pos()
            return event.accept()
        
        return event.ignore()


    def mouseReleaseEvent(self, event:QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_pressed:
            self._is_pressed = False
            if (event.pos() - self._pressed_pos).manhattanLength() < 10:
                self.clicked.emit()
            return event.accept()
        return event.ignore()
    
    def paintEvent(self, event:QPaintEvent):
        painter = QPainter(self)        
        painter.setBrush(QColor(100,100,100))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawRoundedRect(self.rect(), 4, 4)

        super().paintEvent(event)


class PanelWidgetBase(QWidget):
    def __init__(self, parent_area:'MultiColumnWidget', index:int):
        super().__init__()

        self._parent_area = parent_area

        self._header_widget = PanelHeader("Header")
        self._layout = QVBoxLayout(self)

        self._layout.setContentsMargins(0,0,0,0)

        self._layout.addWidget(self._header_widget)
        self._contents = QWidget()
        self._layout.addWidget(self._contents)

        self.ui = Ui_Panel01()
        self.ui.setupUi(self._contents)

        w = self._contents.findChild(QObject, "isApple")
        self._header_widget.clicked.connect(lambda: self.set_content_collapse(not self._contents.isHidden()))

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def paintEvent(self, event:QPaintEvent):
        painter = QPainter(self)        
        painter.setBrush(QColor(128,128,128))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawRoundedRect(self.rect(), 4, 4)

        super().paintEvent(event)

    def set_content_collapse(self, is_collapse:bool):
        self._contents.setHidden(is_collapse)
        self._parent_area.distribute_items()


class ColumnScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        container = QWidget()
        self.setWidget(container)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0,0,0,0)
        container.setLayout(self._layout)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setFrameShape(QFrame.Shape.NoFrame)

        # パニング用状態
        self._panning = False
        self._pan_start = QPoint()
        self._v_scroll_start = 0

    def add_item(self, widget):
        self._layout.addWidget(widget)

    def clear_items(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)


class MultiColumnWidget(QWidget):

    _MIN_COLUMN_WIDTH = 400
    _MAX_COLUMNS = 5
    _OVERFLOW_VISIBLE_THRESHOLD = 0.5
    _MIN_VISIBLE_PIXELS = 40

    def __init__(self):
        super().__init__()

        self._panels:list[PanelWidgetBase] = []
        self._is_panning  = False
        self._drag_origin_pos:QPoint|None = None
        self._drag_target_scroll_area:ColumnScrollArea|None = None

        self._layout = QHBoxLayout(self)
        # self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self.setContentsMargins(4,4,4,4)

        self._columns:list[ColumnScrollArea] = []
        for _ in range(self._MAX_COLUMNS):
            column = ColumnScrollArea(self)
            self._columns.append(column)
            self._layout.addWidget(column)

        for widget in self.findChildren(QWidget):
            widget:QWidget
            widget.installEventFilter(self)

        self._adjust_column_visibility()

    def showEvent(self, event):
        super().showEvent(event)
        self._adjust_column_visibility()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_column_visibility()

    def add_panel(self, panel:PanelWidgetBase):
        """パネルを追加"""
        self._panels.append(panel)

        for widget in panel.findChildren(QWidget):
            widget:QWidget
            widget.installEventFilter(self)

        self.distribute_items()

    def _adjust_column_visibility(self):

        available_width = self.width()
        max_columns_fit = max(1, min(self._MAX_COLUMNS, available_width // self._MIN_COLUMN_WIDTH))
        for i, column in enumerate(self._columns):
            column.setHidden(i >= max_columns_fit)

        self.distribute_items()

    def get_shown_column_scroll_areas(self)->list[ColumnScrollArea]:
        return [col for col in self._columns if not col.isHidden()]

    def distribute_items(self):
        shown = self.get_shown_column_scroll_areas()
        if not shown:
            return

        last_index = len(shown) - 1

        #─── 1) 事前キャッシュ ────────────────────────────────
        layouts:list[QVBoxLayout] = [col.widget().layout() for col in shown]
        view_h = [col.viewport().height() for col in shown]
        spacings = [lay.spacing() for lay in layouts]
        panel_h = [p.sizeHint().height() for p in self._panels]

        #─── 2) 配置先計算 ────────────────────────────────
        assignment = [0] * len(self._panels)
        col_index = 0
        curr_h = 0
        min_pixels = self._MIN_VISIBLE_PIXELS
        threshold = self._OVERFLOW_VISIBLE_THRESHOLD

        for i, p in enumerate(self._panels):
            ph = panel_h[i] if not p.isHidden() else 0
            sp = spacings[col_index] if layouts[col_index].count() > 0 else 0
            incr = ph + (0 if i == 0 else sp)

            if i > 0:
                # はみ出す前に判定
                if curr_h + ph > view_h[col_index] and col_index < last_index:
                    overflow = curr_h + ph - view_h[col_index]
                    visible_height = ph - overflow
                    vis_ratio = (visible_height / ph) if ph > 0 else 1.0

                    # 「見えている割合 or 絶対高さ」のいずれも不足なら次列
                    if vis_ratio < threshold or visible_height < min_pixels:
                        col_index += 1
                        curr_h = 0
                        incr = ph  # 新列は spacing なし

            assignment[i] = col_index
            curr_h       += incr

        #─── 3) 再配置 ────────────────────────────────────
        for idx, layout in enumerate(layouts):
            target_widget = shown[idx].widget()
            desired = [p for p, c in zip(self._panels, assignment) if c == idx]
            for pos, panel in enumerate(desired):
                item = layout.itemAt(pos)
                if item and item.widget() is panel:
                    continue
                panel.setParent(target_widget)
                layout.insertWidget(pos, panel)


    def _scroll_area_at_pos(self, pos: QPoint) -> ColumnScrollArea | None:
        for area in self._columns:
            if not area.isVisible():
                continue
            rect = QRect(area.pos(), area.size())
            if rect.contains(pos):
                return area
        return None
    
    def _set_scroll_area_value(self, scroll_area:QScrollArea, event:QWheelEvent):
        value = 15
        value *= 1 if event.delta() > 0 else -1
        bar = scroll_area.verticalScrollBar()
        bar.setValue(bar.value() - value)

    def eventFilter(self, watched, event: QEvent):
        if not isinstance(watched, QWidget):
            return False

        if isinstance(event, QWheelEvent) and event.type() == QEvent.Type.Wheel:
            pos = watched.mapTo(self, event.position().toPoint())
            column = self._scroll_area_at_pos(pos)
            if column is not None:
                self._set_scroll_area_value(column, event)
            return True

        elif isinstance(event, QMouseEvent):
            pos = watched.mapTo(self, event.pos())

            # 中ボタン押下 → パン開始
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.MiddleButton:
                column = self._scroll_area_at_pos(pos)
                if column is not None:
                    self._is_panning = True
                    self._drag_origin_pos = pos
                    self._drag_target_scroll_area = column
                return True

            # パン中の処理
            if self._is_panning and self._drag_origin_pos and self._drag_target_scroll_area:
                if event.type() == QEvent.Type.MouseMove:
                    delta_y = pos.y() - self._drag_origin_pos.y()
                    bar = self._drag_target_scroll_area.verticalScrollBar()
                    bar.setValue(bar.value() - delta_y)
                    self._drag_origin_pos = pos
                    return True

                elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.MiddleButton:
                    self._is_panning = False
                    self._drag_origin_pos = None
                    self._drag_target_scroll_area = None
                    return True

        return False

# 動作確認用
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_widget = MultiColumnWidget()

    for i in range(6):
        panel = PanelWidgetBase(main_widget, i)
        # if i % 2 == 0:
        #     panel.setHidden(True)
        main_widget.add_panel(panel)

    main_widget.resize(800, 600)
    main_widget.show()

    sys.exit(app.exec_())
