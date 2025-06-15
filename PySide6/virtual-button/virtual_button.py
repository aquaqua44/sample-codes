from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QVBoxLayout, QApplication, QScrollArea, QHBoxLayout, QMainWindow, QFrame
from PySide6.QtCore import QPoint, Signal, Qt, QObject, QEvent, QSize
from PySide6.QtGui import QPaintEvent, QPainter, QBrush, QColor, QPen, QRegion
import random, string

from drag_widget import DragAreaBase, DragItemBase

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRect, Qt, Signal, QPoint, QMargins, QTimer
from PySide6.QtGui import (
    QPainter, QFontMetrics, QMouseEvent, QColor, QResizeEvent, 
    QPen, QBrush, QPaintEvent, QStaticText, QTransform, QLinearGradient, QFont
)

import time


PROJECT_COUNT = 4
USER_COUNT = 10
GROUP_COUNT = 10

def generate_random_items(num_items, prefix=""):
    num_items = random.randint(2, 6)
    items = []

    for i in range(1, num_items + 1):
        item_id = f"id{i:04d}"
        name_length = random.randint(1, 5)
        name = ''.join(random.choices(string.ascii_letters, k=name_length))
        items.append((item_id, f"{prefix} {name}"))

    return items

class VirtualBuittonHeader:

    @property
    def header_size(self)->QSize:
        return self._header_size
    
    @property
    def parent_header_height(self)->int:
        return self._parent_header_height
    
    @property
    def button_data(self)->tuple[str, QStaticText, int, QRect]:
        return self._button_data

    def __init__(self, item_widget:QWidget, header_min_height:int, margin:QMargins, parent=None):

        self._item_widget = item_widget
        self._min_header_height = header_min_height

        self._header_size:QSize = QSize(0,0)
        self._parent_header_height = 0

        """
        プロパティ
        """

        # レイアウト設定
        
        self._button_padding_x = 10
        self._button_height = 16
        self._button_max_width = 200

        # コンテンツアイテムマージン
        self._content_item_margin = margin

        # ボタンレイアウト設定
        self._margin_left = 10
        self._margin_top = 6
        self._margin_right = 10
        self._margin_bottom = 10
        self._layout_spacing_x = 4
        self._layout_spacing_y = 4

        self._title_padding_x = 10

        self._title_font = QFont("Yu Gothic", 10)
        self._title_font.setBold(True)

        self._button_font = QFont("Yu Gothic", 8)
        self._button_font.setBold(False)

        
        """
        変数66
        """
        # ヘッダー

        self._header_pos_y = 0
        self._before_pos_y = 0

        self._parent_header_height = 0

        self._title = ""
        self._title_width = 0
        self._button_data = []

        self._mouse_press_pos: None | QPoint = None
        self._is_mouse_pressed = False
        self._current_index = -1
        self._is_title_hover = False

        self._button_bg_color = QColor(230,230,230)
        self._button_hover_bg_color = self._button_bg_color.lighter(120)
        self._button_press_bg_color = self._button_bg_color.darker(120)

    def set_parent_header_height(self, height:int):
        self._parent_header_height = height



    def set_title(self, title:str):
        """タイトルを設定"""
        self._title = title
        fm = QFontMetrics(self._title_font)
        self._title_width = fm.horizontalAdvance(title) + 10

    def set_buttons(self, button_data:list):
        """ボタンデータからボタン情報を生成"""
        self._button_data.clear()
        fm = QFontMetrics(self._button_font)

        for btn_id, text in button_data:
            max_content_width = self._button_max_width - self._button_padding_x * 2
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max_content_width)

            static_text = QStaticText(elided)
            static_text.setTextFormat(Qt.TextFormat.PlainText)
            static_text.prepare(QTransform(), self._button_font)

            display_width = fm.horizontalAdvance(elided)
            total_width = display_width + self._button_padding_x * 2
            total_width = min(total_width, self._button_max_width)

            self._button_data.append((btn_id, static_text, total_width, QRect(0, 0, total_width, self._button_height)))


class ProjectItem(DragItemBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_height()

    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(150, 150, 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.end()
    
    def set_height(self):
        height = random.randint(24,72)
        self.setFixedHeight(height) #　アイテムの高さ

    def mousePressEvent(self, event):
        print("ProjectItem Clicked")
        event.accept()
        # return super().mousePressEvent(event)


class ProjectArea(DragAreaBase):

    def __init__(self, parent=None):
        super().__init__(ProjectItem)
        

    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(220, 220, 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        painter.end()

class UserItem(VirtualBuittonHeader, DragItemBase):
    def __init__(self, item_id:str, item_name:str, parent=None):
        DragItemBase.__init__(self, parent=parent)
        VirtualBuittonHeader.__init__(self, self, 24, QMargins(20,0,0,20))

        layout = QVBoxLayout(self)
        self._area = ProjectArea()

        layout.addWidget(self.area)

        
        button_data = generate_random_items(PROJECT_COUNT, "Project")

        for i, k in button_data:
            item = ProjectItem()
            self._area.add_item(item)

        self.set_buttons(button_data)


    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(150, 255, 150)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.end()
    

class UserArea(DragAreaBase):

    def __init__(self, parent=None):
        super().__init__(UserItem)
        
        self.layout().setContentsMargins(0,0,0,0)

    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(220, 255, 220)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        painter.end()


class GroupItem(VirtualBuittonHeader, DragItemBase):
    """
    グループアイテム 中に ユーザーアイテム
    """
    def __init__(self, parent=None):
        DragItemBase.__init__(self, parent=parent)
        VirtualBuittonHeader.__init__(self, self, 24, QMargins(0,0,0,20))
        
        layout = QVBoxLayout(self)
        self._area = UserArea()

        layout.addWidget(self.area)

        button_data = generate_random_items(USER_COUNT, "User")

        for i, k in button_data:
            item = UserItem(i, k)
            self._area.add_item(item)

        self.set_buttons(button_data)


    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(250, 150, 150)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.end()


class GroupArea(DragAreaBase):

    def __init__(self, parent=None):
        super().__init__(GroupItem)

        self.layout().setContentsMargins(0,0,0,0)
        
        "グループアイテム作成"
        for i in range(GROUP_COUNT):
            item = GroupItem()
            self.add_item(item)

    def paintEvent(self, event:QPaintEvent):

        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(255, 220, 220)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        painter.end()



class CustomScrollArea(QScrollArea):
    size_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def resizeEvent(self, arg__1):
        self.size_changed.emit()
        return super().resizeEvent(arg__1)



class HeaderPainter(QWidget):
    def __init__(self, scroll_area:CustomScrollArea):
        super().__init__(parent=scroll_area.viewport())
        self._scroll_area = scroll_area
        self._scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        self._viewport = scroll_area.viewport()
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)

        self._curren_button = (None, None) 

        # サイズ変更時 ボタン列変更
        scroll_area.size_changed.connect(self._fit_viewport)
        self._scroll_area.verticalScrollBar().valueChanged.connect(self.paint_header)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_finished)

        self._on_resize_finished()

    def _on_resize_finished(self):

        items = self.get_virtual_button_header_items(first_cls=GroupItem)

        for item in items:
            self.layout_buttons(item)
        widget = self._scroll_area.widget()

        widget.updateGeometry()
        widget.adjustSize()  


        widget.updateGeometry()
        widget.adjustSize()  

        self.paint_header()

        self.update()
    
    def _fit_viewport(self):
        
        self.setGeometry(self._viewport.geometry())
        self._resize_timer.start(100)

    
    def layout_buttons(self, item:VirtualBuittonHeader|DragItemBase):
        """各ボタンのrectとヘッダーの高さを計算。"""

        header_width = item.width()
        
        # マージンなどのレイアウト用変数
        x_margin = item._title_padding_x + item._title_width + item._margin_left
        top_margin = item._margin_top
        right_margin = item._margin_right
        bottom_margin = item._margin_bottom
        spacing_x = item._layout_spacing_x
        spacing_y = item._layout_spacing_y
        line_height = item._button_height

        # === 1. 行ごとにグループ化 ===
        lines = []
        current_line = []
        current_line_width = x_margin

        for btn_id, static_text, width, _ in item._button_data:
            fits = current_line and (current_line_width + width + right_margin > header_width)
            if fits:
                lines.append(current_line)
                current_line = []
                current_line_width = x_margin

            current_line.append((btn_id, static_text, width))
            current_line_width += width + spacing_x

        if current_line:
            lines.append(current_line)

        # === 2. 行単位で QRect を生成 ===
        y = top_margin
        new_buttons = []

        for line in lines:
            x = x_margin
            for btn_id, static_text, width in line:
                rect = QRect(x, y, width, line_height)
                new_buttons.append((btn_id, static_text, width, rect))
                x += width + spacing_x
            y += line_height + spacing_y

        # === 3. 結果を反映 ===
        item._button_data = new_buttons
        header_height = y + bottom_margin - spacing_y
        header_height = max(header_height, item._min_header_height)

        item._header_size = QSize(header_width, header_height)

        parent_item = item.area.parent()
        if isinstance(parent_item, VirtualBuittonHeader):
            item.set_parent_header_height(parent_item.header_size.height())

        margin = item._content_item_margin + QMargins(0, header_height, 0, 0)
        item._item_widget.layout().setContentsMargins(margin)


    def mousePressEvent(self, event):
        print("header_clicked")
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event:QMouseEvent):

        item = self._scroll_area.widget().childAt(event.position().toPoint())
        pos = event.position().toPoint()
        target_item = None
        for item, item_rect in reversed(list(self._virtual_header_items.items())):
            if item_rect.contains(pos):
                target_item = item
                break
        
        target_id = None
        for btn_id, static_text, width, button_rect in item.button_data:
            button_rect:QRect
            button_rect = button_rect.translated(0, item_rect.y())

            if button_rect.contains(pos):
                target_id = btn_id
                break

        self._curren_button = (target_item, target_id)

        self.update()
    
    def get_virtual_button_header_items(self, first_cls=UserItem)->list[VirtualBuittonHeader|DragItemBase]:
        items:list = self._scroll_area.findChildren(VirtualBuittonHeader)
        items.sort(key=lambda obj: not isinstance(obj, first_cls))
        return items

    def get_visible_items(self) -> dict[VirtualBuittonHeader|DragItemBase, QRect]:
        viewport = self._scroll_area.viewport()
        vp_height = viewport.height()
        visible_items = {}

        # UserItem を一度だけキャッシュしておくとさらに高速
        for item in self.get_virtual_button_header_items():
            item:VirtualBuittonHeader|DragItemBase
            if not item.isVisible():
                continue

            # item の左上 (0,0) を viewport 座標系にマップ
            y_in_vp = item.mapTo(viewport, QPoint(0, 0)).y()
            item_h = item.height()

            # 「少しでも見えていれば可視」とみなす
            if y_in_vp + item_h >= 0 and y_in_vp <= vp_height:
                visible_items[item] = QRect(0,0,0,0)


        return visible_items
    
    def paint_header(self):
        # start = time.perf_counter()
        self._virtual_header_items = self.get_visible_items()
        
        region = QRegion()
        for item in self._virtual_header_items:
            pos_in_viewport = item.mapTo(self._viewport, item.rect().topLeft())
            view_y = pos_in_viewport.y()


            if view_y - item.parent_header_height < 0:
                pos_y = view_y * -1
                max_pos_y = item.height() - item.header_size.height() - item.parent_header_height
                pos_y = pos_y if pos_y < max_pos_y else max_pos_y
                header_pos_y = pos_y + item.parent_header_height

            else:
                header_pos_y = 0


            header_rect = QRect(pos_in_viewport + QPoint(0, header_pos_y), item.header_size)
            self._virtual_header_items[item] = header_rect
            region += QRegion(header_rect)

        self.setMask(region)

        # end = time.perf_counter()
        # elapsed_ms = (end - start) * 1000
        # print(f"処理時間: {elapsed_ms:.3f} ミリ秒")
        self.update()

    def draw_button(self, painter:QPainter, item:VirtualBuittonHeader, y_offset:int):

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fm = QFontMetrics(self.font())


        for btn_id, static_text, width, rect in item.button_data:
            if (item, btn_id) == self._curren_button:
                # painter.setBrush(self._button_hover_bg_color)
                painter.setBrush(QColor(220,220,220))
                # if self._is_mouse_pressed:
                #     painter.setBrush(self._button_press_bg_color)
                # else:
                #     painter.setBrush(self._button_hover_bg_color)
            else:
                # painter.setBrush(self._button_bg_color)
                painter.setBrush(QColor(255,255,255))

            rect:QRect

            # painter.setBrush(QColor(255,255,255))

            rect = rect.translated(0, y_offset)

            painter.setPen(QPen(QColor(100, 100, 100)))
            radius = int(item._button_height / 2)
            painter.drawRoundedRect(rect, radius, radius)

            text_x = rect.left() + item._button_padding_x
            text_y = rect.top() + (rect.height() - fm.height()) // 2
            painter.drawStaticText(text_x, text_y, static_text)


    def paintEvent(self, event:QPaintEvent):

        painter = QPainter(self)

        for item, rect in self._virtual_header_items.items():
            if isinstance(item, GroupItem):
                painter.setBrush(QBrush(QColor(255, 10, 10)))
            else:
                painter.setBrush(QBrush(QColor(10, 255, 10)))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)

            self.draw_button(painter, item, rect.y())

        # 背景の描画
        
        # painter.setBrush(QBrush(QColor(255, 255, 0)))
        # painter.setPen(Qt.PenStyle.NoPen)
        # painter.drawRect(self.rect())
        # painter.end()


class ScrollAreaTest(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QVBoxLayout(self)

        self._scroll_area = CustomScrollArea()
        self._scroll_area.setWidgetResizable(True)

        layout.addWidget(self._scroll_area)
        content_widget = QWidget()        
        self._scroll_area.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.addWidget(GroupArea())

        header_painter = HeaderPainter(self._scroll_area)
        header_painter.raise_()
