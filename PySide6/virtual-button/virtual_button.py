from PySide6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QApplication, QScrollArea, QLabel, QSizePolicy, QHBoxLayout, QPushButton
from PySide6.QtCore import QPoint, Signal, Qt, QRect, QTimer

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRect, Qt, Signal, QPoint, QMargins
from PySide6.QtGui import (
    QPainter, QFontMetrics, QMouseEvent, QColor, QResizeEvent, 
    QPen, QBrush, QPaintEvent, QStaticText, QTransform, QLinearGradient, QFont

)

import random
import string

class HeaderShadow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        shadow_height = 10

        # 高さ設定
        self.setFixedHeight(shadow_height)

        # マウスイベントに対して透過
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # 影作成
        gradient = QLinearGradient(0, 0, 0, shadow_height)
        gradient.setColorAt(0.0, QColor(0,0,0,100))
        gradient.setColorAt(1.0, QColor(0,0,0,0))

        self._brush = QBrush(gradient)

    def paintEvent(self, event):
        painter = QPainter(self)        
        painter.setBrush(self._brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

class VirtualBuittonHeaderBase(QWidget):

    button_clicked = Signal(str)

    def __init__(self, item_widget:QWidget, scroll_area:QScrollArea, header_min_height:int, margin:QMargins, is_shadow, parent=None):
        super().__init__(parent)

        self._item_widget = item_widget
        self._scroll_area = scroll_area
        self._viewport = scroll_area.viewport()
        self._min_header_height = header_min_height

        self._is_shadow = is_shadow

        """
        プロパティ
        """

        # ヘッダー
        self._shadow_height = header_min_height

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

        """
        変数66
        """
        # ヘッダー

        self._header_height = self._min_header_height

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

        """
        初期化
        """
        if self._is_shadow:
            self._shadow = HeaderShadow(parent=item_widget)
            self._shadow.raise_()

        item_widget.resized.connect(self._set_size)
        self.raise_() # ヘッダーウィジェットを前面に表示

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_finished)

        scroll_area.verticalScrollBar().valueChanged.connect(self._set_header_pos)
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        for i in range(15):
            layout.addWidget(QPushButton(f"ボタン{i}"))


    def scroll_to_item(self, item:QWidget):
        
        if item is None:
            return
        in_viewport_pos = item.mapFrom(self._scroll_area.widget(), QPoint(0,0))
        y = -in_viewport_pos.y() - self._header_height - self._parent_header_height - self._content_item_margin.top()
        self._scroll_area.verticalScrollBar().setValue(y)

    def _set_size(self, width:int):
        """ヘッダーリサイズ（即時）"""
        self.setFixedWidth(width)
        if self._is_shadow:
            self._shadow.setFixedWidth(width)
        self._resize_timer.start(100)

    def _on_resize_finished(self):
        """ヘッダーリサイズ（遅延）"""
        self.layout_buttons()
        self._set_header_pos()

    def leaveEvent(self, event):
        self._is_mouse_pressed = False
        self._current_index = -1
        self._is_title_hover = False
        self.update()
        return super().leaveEvent(event)

    def set_title(self, title:str):
        self._title = title
        fm = QFontMetrics(self._title_font)
        self._title_width = fm.horizontalAdvance(title) + 10

    def set_buttons(self, button_data:list):
        self._button_data.clear()
        fm = QFontMetrics(self.font())

        for btn_id, text in button_data:
            max_content_width = self._button_max_width - self._button_padding_x * 2
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max_content_width)

            static_text = QStaticText(elided)
            static_text.setTextFormat(Qt.TextFormat.PlainText)
            static_text.prepare(QTransform(), self.font())

            display_width = fm.horizontalAdvance(elided)
            total_width = display_width + self._button_padding_x * 2
            total_width = min(total_width, self._button_max_width)

            self._button_data.append((btn_id, static_text, total_width, QRect(0, 0, total_width, self._button_height)))

        self.update()

    def layout_buttons(self):

        max_width = self.width()
        
        # マージンなどのレイアウト用変数
        x_margin = self._title_padding_x + self._title_width + self._margin_left
        top_margin = self._margin_top
        right_margin = self._margin_right
        bottom_margin = self._margin_bottom
        spacing_x = self._layout_spacing_x
        spacing_y = self._layout_spacing_y
        line_height = self._button_height

        # === 1. 行ごとにグループ化 ===
        lines = []
        current_line = []
        current_line_width = x_margin

        for btn_id, static_text, width, _ in self._button_data:
            fits = current_line and (current_line_width + width + right_margin > max_width)
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
        self._button_data = new_buttons
        header_height = y + bottom_margin - spacing_y
        self._header_height = max(header_height, self._min_header_height)

        self.setFixedHeight(self._header_height)

        margin = self._content_item_margin + QMargins(0, self._header_height, 0, 0)
        self._item_widget.layout().setContentsMargins(margin)
        self._set_header_pos()
            
    def _get_button_data_by_pos(self, pos: QPoint):
        for button_data in self._button_data:
            rect: QRect = button_data[3]
            if rect.contains(pos):
                return button_data
        return None

    def _get_current_button(self):
        if -1 < self._current_index < len(self._button_data):
            return self._button_data[self._current_index]
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._mouse_press_pos = pos
            self._is_mouse_pressed = True
            self.update()
            return event.accept()

        else:
            return event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        self._current_index = -1
        self._is_title_hover = False

        if pos.x() < self._title_width:
            self._is_title_hover = True
            self.update()
            return 
        
        for i, (_, _, _, rect) in enumerate(self._button_data):
            rect:QRect
            if rect.contains(pos):
                self._current_index = i
                break

        self.update()
        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):

        if not self._is_mouse_pressed:
            return event.ignore()

        else:
            pos = event.position().toPoint()
            if (pos - self._mouse_press_pos).manhattanLength() < 10:
                button_data = self._get_current_button()
                if button_data is not None:
                    button_id, _, _, _ = button_data
                    self.button_clicked.emit(button_id)
            self._mouse_press_pos = None
            self._is_mouse_pressed = False
            self.update()
            return event.accept()


    def _set_header_pos(self):

        rect = self._item_widget.rect()
        pos_in_viewport = self._item_widget.mapTo(self._viewport, rect.topLeft())
        is_visible = self._viewport.rect().intersects(QRect(pos_in_viewport, rect.size()))

        if not is_visible:
            return
        
        view_y = pos_in_viewport.y()

        if view_y == self._before_pos_y:
            return

        self._before_pos_y = view_y

        if view_y - self._parent_header_height < 0:
            pos_y = view_y * -1
            max_pos_y = self._item_widget.height() - self._header_height - self._parent_header_height
            pos_y = pos_y if pos_y < max_pos_y else max_pos_y
            self._header_pos_y = pos_y + self._parent_header_height
            self.move(0, self._header_pos_y)

            if self._is_shadow:
                self._shadow.move(0, self._header_pos_y+self._header_height)

        else:
            self._header_pos_y = 0
            self.move(0, 0)
            if self._is_shadow:
                self._shadow.move(0, 0)

        self.update()

    def draw_button(self, painter:QPainter):

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fm = QFontMetrics(self.font())

        for index, (btn_id, static_text, width, rect) in enumerate(self._button_data):
            if index == self._current_index:
                if self._is_mouse_pressed:
                    painter.setBrush(self._button_press_bg_color)
                else:
                    painter.setBrush(self._button_hover_bg_color)
            else:
                painter.setBrush(self._button_bg_color)

            rect:QRect

            painter.setPen(QPen(QColor(100, 100, 100)))
            radius = int(self._button_height / 2)
            painter.drawRoundedRect(rect, radius, radius)

            text_x = rect.left() + self._button_padding_x
            text_y = rect.top() + (rect.height() - fm.height()) // 2
            painter.drawStaticText(text_x, text_y, static_text)


    def paintEvent(self, event:QPaintEvent):
        painter = QPainter(self)

        painter.setPen(Qt.PenStyle.NoPen)

        # 背景

        width = self.width()
        height = self.height()

        gradient = QLinearGradient(0, 0, 0, height)
        color = QColor(240,240,240)
        gradient.setColorAt(0.0, color)
        gradient.setColorAt(3 / height, color.darker(108))
        gradient.setColorAt((height - 3) / height, color.darker(115))
        gradient.setColorAt(1.0, color.darker(150))

        painter.setBrush(gradient)
        rect = QRect(0,0, width, height)
        painter.drawRect(rect)

        # タイトル
        title_rect = QRect(0, 0, self._title_padding_x + self._title_width, height)
        if self._is_title_hover:
            color = QColor(0,0,0,60) if self._is_mouse_pressed else QColor(0,0,0,15)
            painter.setBrush(color)
            painter.drawRect(title_rect)

        painter.setPen(QColor(10,10,10))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setFont(self._title_font)
        rect = title_rect.adjusted(self._title_padding_x, self._margin_top, 0, -self._margin_bottom)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter, self._title)

        painter.setFont(self.font())
        self.draw_button(painter)


class ItemBase(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._layout = QVBoxLayout(self)

        self._layout.setContentsMargins(0,0,0,0)
        self.setContentsMargins(0,0,0,0)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def add_item(self, item:QWidget):
        self._layout.addWidget(item)

    def get_items(self)->list['ItemBase']:
        items = []
        for i in range(self._layout.count()):
            items.append(self._layout.itemAt(i).widget())

        return items
    
    def generate_random_items(self):
        num_items = random.randint(5, 30)
        items = []

        for i in range(1, num_items + 1):
            item_id = f"id{i:04d}"
            name_length = random.randint(5, 30)
            name = ''.join(random.choices(string.ascii_letters, k=name_length))
            items.append((item_id, name))
        return items
    

class UserHeader(VirtualBuittonHeaderBase):
    def __init__(self, item_widget, scroll_area, parent=None):
        margin = QMargins(10,10,0,10)
        super().__init__(item_widget, scroll_area, 30, margin,True, parent=parent)
        self._margin_bottom = 6
        self._margin_top = 6

class UserItem(ItemBase):
   
    resized = Signal(int)

    def __init__(self, scroll_area:QScrollArea, parent=None):
        ItemBase.__init__(self, parent)

        self._scroll_area = scroll_area

        self._layout.setSpacing(10)

        # プロパティ
        items = self.generate_random_items()

        for item in items:
            label = QLabel(item[1])
            label.setObjectName(item[0])
            height = random.randint(50, 250)
            label.setFixedHeight(height)
            self.add_item(label)


        self._header_widget = UserHeader(self, scroll_area, parent=self)
        self._header_widget.set_title("User")
        self._header_widget.set_buttons(items)
        self._header_widget.button_clicked.connect(self.scroll_to_item)


    def scroll_to_item(self, item_id):
        item = None
        item:QLabel = self.findChild(QLabel, item_id)
        if item is None:
            return
        self._header_widget.scroll_to_item(item)


    def resizeEvent(self, event:QResizeEvent):
        self.resized.emit(event.size().width())
        return super().resizeEvent(event)

    def paintEvent(self, event:QPaintEvent):
        
        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(200, 200, 200, 100)))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(self.rect())

        painter.end()


class GroupHeader(VirtualBuittonHeaderBase):
    def __init__(self, item_widget, scroll_area, parent=None):
        super().__init__(item_widget, scroll_area, 30, QMargins(0,0,0,0), False, parent)
        self._item_widget:GroupItem = item_widget

    def layout_buttons(self):
        super().layout_buttons()
        for item in self._item_widget.get_items():
            if isinstance(item, UserItem):
                item._header_widget._parent_header_height = self._header_height

class GroupItem(ItemBase):
   
    resized = Signal(int)

    def __init__(self, scroll_area:QScrollArea, parent=None):
        ItemBase.__init__(self, parent)

        self.setFixedWidth(10000)

        self._scroll_area = scroll_area        

        # プロパティ
        items = self.generate_random_items()

        self._color = self.random_colorful_qcolor()

        self._layout.setSpacing(0)

        for item in items:
            user_item = UserItem(scroll_area)
            user_item.setObjectName(item[0])
            self.add_item(user_item)

        self._header_widget = GroupHeader(self, scroll_area, parent=self)
        self._header_widget.set_title("グループ")

        self._header_widget.set_buttons(items)
        self._header_widget.button_clicked.connect(self.scroll_to_item)

    def scroll_to_item(self, item_id):
        item = None
        item:QLabel = self.findChild(UserItem, item_id)
        if item is None:
            return
        self._header_widget.scroll_to_item(item)

    def random_colorful_qcolor(self):
        # 色相 (Hue): 0〜359度
        h = random.randint(0, 359)
        # 彩度 (Saturation)・明度 (Value) を高めに設定
        s = 255
        v = 200
        return QColor.fromHsv(h, s, v)


    def resizeEvent(self, event:QResizeEvent):
        self.resized.emit(event.size().width())
        return super().resizeEvent(event)

    def paintEvent(self, event:QPaintEvent):
        # 背景の描画
        painter = QPainter(self)
        painter.setBrush(self._color)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        painter.end()





import time

class InertialScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setWidgetResizable(True)

        # スクロール状態
        self._dragging = False
        self._last_pos = QPoint()
        self._velocity = QPoint()
        self._last_time = 0

        # 慣性スクロール用タイマー
        self._inertia_timer = QTimer()
        self._inertia_timer.timeout.connect(self._perform_inertia_scroll)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._dragging = True
            self._last_pos = event.position().toPoint()
            self._velocity = QPoint()
            self._last_time = time.time()
            self._inertia_timer.stop()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            current_pos = event.position().toPoint()
            delta = current_pos - self._last_pos
            current_time = time.time()
            dt = current_time - self._last_time

            if dt > 0:
                self._velocity = delta / dt

            self._last_pos = current_pos
            self._last_time = current_time

            # スクロール位置を更新
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self._dragging:
            self._dragging = False
            self._inertia_timer.start(16)  # 約60FPS
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _perform_inertia_scroll(self):
        # 慣性スクロールの実行
        friction = 0.90  # 摩擦係数
        self._velocity *= friction

        if abs(self._velocity.x()) < 0.5 and abs(self._velocity.y()) < 0.5:
            self._inertia_timer.stop()
            return

        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(self._velocity.x()))
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(self._velocity.y()))




class StickyHeaderSample(QWidget):
    def __init__(self):
        super().__init__()

        self.resize(1920, 1080)
        layout = QVBoxLayout(self)

        scroll_area = InertialScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0,0,0,0)
        scroll_area.setWidget(content_widget)

        self.setStyleSheet("""
        QLabel {
            margin: 0;
            padding: 5px;
            background-color: #3399ff;
            color: white;
            border-radius: 8px;
        }
        """)

        # ラベルに適用
        for i in range(10):
            item = GroupItem(scroll_area)
            content_layout.addWidget(item)
            

if __name__ == "__main__":
    app = QApplication()
    window = StickyHeaderSample()
    window.show()
    app.exec()