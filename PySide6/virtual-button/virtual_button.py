from PySide6.QtWidgets import (
    QApplication, QTreeView, QWidget, QVBoxLayout,
    QHeaderView, QAbstractItemView, QComboBox, QCheckBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QMouseEvent
from PySide6.QtCore import Qt, QModelIndex, Signal
import sys, time

from global_data import GlobalData
from database_manager import DatabaseManager

class CheckTreeView(QTreeView):
    # チェック済み子ノードテキストリストを通知
    item_selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # モデル初期化
        self._model = QStandardItemModel()
        self._model.setColumnCount(2)
        self._model.setHorizontalHeaderLabels(["項目", "ID"])
        super().setModel(self._model)

        # 固定設定
        self.setItemsExpandable(False)
        self.setExpandsOnDoubleClick(False)
        self.setRootIsDecorated(False)

        

    def update_date(self, data: dict[tuple[str, str], list[tuple[str, str]]]):
        """外部データ dict からモデルを再構築し、checked_ids に含まれる子IDをチェック済みにする"""

        scroll_value = self.verticalScrollBar().value()
        checked_ids = self.get_checked_ids()

        self._model.clear()

        for (parent_text, parent_id), children in data.items():
            if not children:
                continue
            # 親アイテム
            p_item = QStandardItem(parent_text)
            p_item.setEditable(False)
            p_item.setCheckable(True)
            p_item.setCheckState(Qt.CheckState.Unchecked)
            p_id = QStandardItem(parent_id)
            p_id.setEditable(False)

            # 子アイテム
            for c_text, c_id in children:
                c_item = QStandardItem(c_text)
                c_item.setEditable(False)
                c_item.setCheckable(True)
                c_item.setCheckState(Qt.CheckState.Checked if c_id in checked_ids else Qt.CheckState.Unchecked)

                c_id_item = QStandardItem(c_id)
                c_id_item.setEditable(False)

                p_item.appendRow([c_item, c_id_item])

            # 親の初期状態を子のチェック状況から設定
            self._update_parent_state(p_item)

            self._model.appendRow([p_item, p_id])

        self.expandAll()
        self.verticalScrollBar().setValue(scroll_value)
        self.setColumnWidth(0,200)

    def set_items_checked(self, checked_ids: list[str]):
        """
        渡された子IDリストに一致するものをチェックON、
        それ以外をチェックOFF にし、親ノード状態も更新する。
        """
        root = self._model.invisibleRootItem()
        for pi in range(root.rowCount()):
            parent = root.child(pi, 0)
            # 子ノードをすべて走査
            for ci in range(parent.rowCount()):
                child = parent.child(ci, 0)
                id_item = parent.child(ci, 1)
                if not child.isCheckable():
                    continue
                # ID一致でチェックON / それ以外OFF
                if id_item.text() in checked_ids:
                    child.setCheckState(Qt.CheckState.Checked)
                else:
                    child.setCheckState(Qt.CheckState.Unchecked)
            # 子を更新したら親ノードの状態を合わせる
            self._update_parent_state(parent)

    def _update_parent_state(self, parent: QStandardItem):
        """ある親アイテムについて子のチェック状況を見て部分/全/無チェックを設定"""
        total = parent.rowCount()
        checked = sum(parent.child(i,0).checkState() == Qt.CheckState.Checked for i in range(total))
        if checked == 0:
            parent.setCheckState(Qt.CheckState.Unchecked)
        elif checked == total:
            parent.setCheckState(Qt.CheckState.Checked)
        else:
            parent.setCheckState(Qt.CheckState.PartiallyChecked)

    def mousePressEvent(self, event: QMouseEvent):
        index = self.indexAt(event.position().toPoint())
        self._on_clicked(index)
        event.accept()

    def _on_clicked(self, index: QModelIndex):
        if not index.isValid():
            return
        # まず 0 列目に揃える
        if index.column() != 0:
            index = index.sibling(index.row(), 0)

        item = self._model.itemFromIndex(index)
        if not item or not item.isCheckable():
            return

        if item.hasChildren():
            # 親項目をクリックした場合
            current = item.checkState()
            if current in (Qt.CheckState.Unchecked, Qt.CheckState.PartiallyChecked):
                new_state = Qt.CheckState.Checked
            else:  # Qt.CheckState.Checked のとき
                new_state = Qt.CheckState.Unchecked
        else:
            # 子項目は従来どおりトグル
            new_state = (
                Qt.CheckState.Checked
                if item.checkState() == Qt.CheckState.Unchecked
                else Qt.CheckState.Unchecked
            )

        # 自分自身に適用
        item.setCheckState(new_state)

        # 親⇔子の同期
        if item.hasChildren():
            # 親クリック → 全子に new_state を適用
            for i in range(item.rowCount()):
                child = item.child(i, 0)
                child.setCheckState(new_state)
        else:
            # 子クリック → 親を再計算
            parent = item.parent()
            if parent:
                self._update_parent_state(parent)

        # チェック済み子ノードIDリストを取得してシグナル発火
        checked = self.get_checked_ids()
        self.item_selection_changed.emit(checked)

    def get_checked_ids(self) -> list[str]:
        checked_ids: list[str] = []
        root = self._model.invisibleRootItem()
        for pi in range(root.rowCount()):
            parent = root.child(pi, 0)
            for ci in range(parent.rowCount()):
                child_item = parent.child(ci, 0)
                if child_item.checkState() == Qt.CheckState.Checked:
                    id_item = parent.child(ci, 1)
                    checked_ids.append(id_item.text())
        return checked_ids




class FilterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(400,800)

        layout = QVBoxLayout(self)

        gd = GlobalData()

        group_datas = gd.get_group_datas()

        self._group_filter_id_combo = QComboBox()
        self._group_filter_id_combo.addItem("")
        self._group_filter_id_combo.addItems(group_datas.keys())        
        layout.addWidget(self._group_filter_id_combo)

        self._group_filter_id_combo.currentIndexChanged.connect(self.update_filter)

        self._is_show_other_group_users = QCheckBox("他グループメンバー表示")
        self._is_show_other_group_users.checkStateChanged.connect(self.update_filter)
        layout.addWidget(self._is_show_other_group_users)

        self._is_show_project_member = QCheckBox("プロジェクト内メンバー表示")
        self._is_show_project_member.checkStateChanged.connect(self.update_filter)
        layout.addWidget(self._is_show_project_member)

        self._is_hide_empty_user_item = QCheckBox("空ユーザーアイテム非表示")
        self._is_hide_empty_user_item.checkStateChanged.connect(self.update_filter)
        layout.addWidget(self._is_hide_empty_user_item)


        self._tree = CheckTreeView()
        self._tree.item_selection_changed.connect(self.update_filter)
        
        layout.addWidget(self._tree)

        self.update_filter()


    def update_filter(self, *args, **kwargs):
        filter_group_id = self._group_filter_id_combo.currentText()
        data = self.create_filter_data(filter_group_id)
        
        
    def create_filter_data(self, filter_group_id:str):

        start = time.time()
        gd = GlobalData()

        user_datas = gd.get_user_datas ()
        group_datas = gd.get_group_datas ()

        project_datas = gd.get_project_datas ()
        time_row_datas = gd.get_time_row_datas()

        # プロパティ
        is_show_other_group_users = self._is_show_other_group_users.isChecked()
        is_show_project_member = self._is_show_project_member.isChecked()
        is_hide_empty_user_item = self._is_hide_empty_user_item.isChecked()

        
        # グループフィルターで取得するユーザーID
        all_data_dict:dict[str, dict[str,dict[str,dict[str:str]]]] = {}
        """
        all_data_dict
        group_id:{
            user_id(pic_user_id):{
                project_id:{
                    time_row_id:user_id
                }
            }
        }
        """

        is_group_filter = (filter_group_id != "" and filter_group_id in group_datas)
        
        for group_id in group_datas.keys():
            all_data_dict[group_id] = {}

        for user_id, user_data in user_datas.items():
            group_id = user_data["group_id"]
            if group_id in all_data_dict:
                all_data_dict[group_id][user_id] = {}

        for project_id, project_data in project_datas.items():
            pic_user_id = project_data["pic_user_id"]
            if pic_user_id in user_datas:
                group_id = user_datas[pic_user_id]["group_id"]
                if group_id in all_data_dict:
                    all_data_dict[group_id][pic_user_id][project_id] = {}

        for time_row_id, time_row_data in time_row_datas.items():
            project_id = time_row_data["project_id"]
            if project_id in project_datas:
                pic_user_id = project_datas[project_id]["pic_user_id"]
                if pic_user_id in user_datas:
                    group_id = user_datas[pic_user_id]["group_id"]
                    if group_id in all_data_dict:
                        user_id = time_row_data["user_id"]
                        if user_id in user_datas:
                            all_data_dict[group_id][pic_user_id][project_id][time_row_id] = user_id

        if not is_group_filter:
            "グループフィルターなし"
            group_filter_target_user_ids = {user_id for user_id, user_data in user_datas.items() if user_data["group_id"] in group_datas}
        else:
            "グループフィルターあり"
            group_filter_target_user_ids = {user_id for user_id, user_data in user_datas.items() if user_data["group_id"] == filter_group_id}

        group_filterd_time_row_dict:dict[str,str|set[str]] = {} # グループフィルター適用時に表示するTimeRowのデータ
        for group_id, users in all_data_dict.items():

            for pic_user_id, projects in users.items():
                for project_id, row_user_data in projects.items():

                    project_member_time_row_ids = set(row_user_data.keys())
                    project_member_user_ids = set(row_user_data.values())

                    if not is_group_filter or group_id == filter_group_id:
                        # フィルターなし、もしくはグループフィルターのターゲットの場合は全て表示

                        group_filterd_time_row_dict.update({
                            k: {
                                "user_id": v,
                                "project_id":project_id,
                                "pic_user_id": pic_user_id,
                                "project_group_id": group_id,
                                "project_member_time_row_ids":set(project_member_time_row_ids),
                                "project_member_user_ids":set(project_member_user_ids),
                            }
                            for k, v in zip(row_user_data.keys(), row_user_data.values())
                        })

                    else:
                        # グループフィルターではない場合
                        if not project_member_user_ids.isdisjoint(group_filter_target_user_ids):
                            # グループフィルター対象外のグループのプロジェクトメンバーにユーザーが含まれる

                            if is_show_other_group_users:
                                # 別グループのプロジェクト内の他のメンバーを表示する

                                group_filterd_time_row_dict.update({
                                    k: {
                                        "user_id": v,
                                        "project_id":project_id,
                                        "pic_user_id": pic_user_id,
                                        "project_group_id": group_id,
                                        "project_member_time_row_ids":set(project_member_time_row_ids),
                                        "project_member_user_ids":set(project_member_user_ids),
                                    }
                                    for k, v in zip(row_user_data.keys(), row_user_data.values())
                                })

                            else:
                                # 別グループプロジェクト内の他のメンバーは表示しない
                                for time_row_id, user_id in row_user_data.items():
                                    if user_id in group_filter_target_user_ids:
                                        group_filterd_time_row_dict[time_row_id] = {
                                            "user_id": user_id,
                                            "project_id":project_id,
                                            "pic_user_id": pic_user_id,
                                            "project_group_id": group_id,
                                            "project_member_time_row_ids":set(project_member_time_row_ids),
                                            "project_member_user_ids":set(project_member_user_ids),
                                        }


        # UserFilterTreeに表示するグループフィルター後のグループ、ユーザーアイテムを設定
        user_filter_model_data:dict[tuple[str],set[str]] = {}
        for time_row_id, data in group_filterd_time_row_dict.items():
            user_id = data["user_id"]
            group_id = user_datas[user_id]["group_id"]
            group_name = group_datas[group_id]["group_name"]
            group_key = (group_name, group_id)
            user_name = user_datas[user_id]["user_name"]
            if group_key not in user_filter_model_data:
                user_filter_model_data[group_key] = set()
            user_filter_model_data[group_key].add((user_name, user_id))
        
        # Treeを設定
        self._tree.update_date(user_filter_model_data)

        # ユーザーフィルター
        user_filter_ids = self._tree.get_checked_ids()
        is_user_filter_on = len(user_filter_ids) > 0
        

        # 表示するtime_row_idとtime_view_user_item_user_idを取得
        show_time_row_id = set()
        show_time_view_user_item_ids = set()
        if is_user_filter_on:
            for time_row_id, data in group_filterd_time_row_dict.items():
                user_id = data["user_id"]
                if user_id in user_filter_ids:
                    show_time_row_id.add(time_row_id) # time_row_id 追加
                    show_time_view_user_item_ids.add(user_id) # user_id 追加

                if is_show_project_member:
                    show_time_row_id = show_time_row_id.union(data["project_member_time_row_ids"]) # time_row_id 追加
                    show_time_view_user_item_ids = show_time_view_user_item_ids.union(data["project_member_user_ids"]) # time_row_id 追加
        else:
            show_time_row_id = set(group_filterd_time_row_dict.keys()) # time_row_id 追加
            show_time_view_user_item_ids = {data["user_id"] for data in group_filterd_time_row_dict.values()}


        # 表示するProjectItemのproject_idを取得
        show_project_dict = {}
        for time_row_id, data in group_filterd_time_row_dict.items():
            project_id = data["project_id"]
            if time_row_id in show_time_row_id and project_id not in show_project_dict:
                show_project_dict[project_id] = {
                    "group_id": data["project_group_id"],
                    "pic_user_id": data["pic_user_id"],
                }
        show_project_ids = set(show_project_dict.keys())

        # 表示するUserItemのuser_idを取得
        show_time_edit_user_item_ids = set()

        if not is_user_filter_on:
            # ユーザーフィルターなし

            if not is_group_filter:
                # グループフィルターなし

                if not is_hide_empty_user_item:
                    # 空アイテムを表示する (全て)
                    for value in all_data_dict.values():
                        show_time_edit_user_item_ids = show_time_edit_user_item_ids.union(set(value.keys()))

                else:
                    # 空アイテムは表示しない

                    # 表示するプロジェクトのpic_user_idのユーザーアイテムを表示する
                    show_time_edit_user_item_ids = {
                        data["pic_user_id"] for data in show_project_dict.values()
                    }

                    # 各グループ従属ユーザー追加
                    show_time_edit_user_item_ids = show_time_edit_user_item_ids.union(
                        {user_id for user_id, user_data in user_datas.items() if user_id == user_data["group_id"]}
                    )

            else:
                # グループフィルターあり
                
                # 表示するプロジェクトのpic_user_idのユーザーアイテムを表示する
                show_time_edit_user_item_ids = {
                    data["pic_user_id"] for data in show_project_dict.values()
                }

                # グループ従属ユーザー追加
                if filter_group_id in user_datas:
                    show_time_edit_user_item_ids.add(filter_group_id)

                # 空アイテムを表示する
                if not is_hide_empty_user_item:
                    show_time_edit_user_item_ids = show_time_edit_user_item_ids.union(group_filter_target_user_ids)
        else:
            # ユーザーフィルターあり
            show_time_edit_user_item_ids = {
                data["pic_user_id"] for data in show_project_dict.values()
            }

        show_time_edit_group_item_ids = {user_datas[user_id]["group_id"] for user_id in show_time_edit_user_item_ids}
        show_time_view_group_item_ids = {user_datas[user_id]["group_id"] for user_id in show_time_view_user_item_ids}

        end = time.time()
        print(f"実行時間：{end - start:.6f} 秒")

        result = {
            "show_time_view_user_item_ids": show_time_view_user_item_ids,
            "show_time_view_group_item_ids": show_time_view_group_item_ids,
            "show_time_edit_group_item_ids": show_time_edit_group_item_ids,
            "show_time_edit_user_item_ids": show_time_edit_user_item_ids,
            "show_project_ids": show_project_ids,
            "show_time_row_id": show_time_row_id,
        }

        return result


if __name__ == "__main__":
    app = QApplication(sys.argv)


    db_filename = r"C:/HukazumiTest/Banana.db"
    db_manager = DatabaseManager()

    db_manager.create_database(db_filename)

    db_manager.init_database(db_filename)

    gd = GlobalData()

    # データベースから取得
    user_datas = db_manager.get_table_id_dict("Users")
    gd.set_user_datas(user_datas)

    group_datas = db_manager.get_table_id_dict("Groups")
    gd.set_group_datas(group_datas)

    project_datas = db_manager.get_table_id_dict("Projects")
    gd.set_project_datas(project_datas)

    time_row_datas = db_manager.get_table_id_dict("TimeRows")
    gd.set_time_row_datas(time_row_datas)

    
    window = FilterWidget()    
    window.show()

    sys.exit(app.exec())
