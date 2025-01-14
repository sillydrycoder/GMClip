import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor
from block_editor.gui.dialogs import LabelDialog
from block_editor.core.label_manager import LabelManager, Label

@pytest.fixture
def label_manager():
    return LabelManager()

@pytest.fixture
def label_dialog(qapp, label_manager):
    return LabelDialog(label_manager)

def test_label_dialog_initialization(label_dialog, label_manager):
    assert label_dialog.label_manager == label_manager
    assert label_dialog.windowTitle() == "Label Manager"
    assert label_dialog.isModal()
    
    # Check if default labels are in the list
    items = [label_dialog.label_list.item(i).text() for i in range(label_dialog.label_list.count())]
    assert any("keep" in item for item in items)
    assert any("remove" in item for item in items)

def test_label_dialog_add_label(label_dialog, qtbot):
    # Set up new label data
    label_dialog.name_edit.setText("test_label")
    label_dialog.hotkey_edit.setText("t")
    label_dialog.current_color = QColor("#FF00FF")
    
    # Click add button
    add_button = next(btn for btn in label_dialog.findChildren(QPushButton) if btn.text() == "Add Label")
    qtbot.mouseClick(add_button, Qt.LeftButton)
    
    # Check if label was added
    items = [label_dialog.label_list.item(i).text() for i in range(label_dialog.label_list.count())]
    assert any("test_label" in item for item in items)
    
    # Check if fields were cleared
    assert label_dialog.name_edit.text() == ""
    assert label_dialog.hotkey_edit.text() == ""

def test_label_dialog_remove_label(label_dialog, qtbot):
    # Add a test label first
    label_dialog.name_edit.setText("test_label")
    label_dialog.hotkey_edit.setText("t")
    label_dialog.current_color = QColor("#FF00FF")
    add_button = next(btn for btn in label_dialog.findChildren(QPushButton) if btn.text() == "Add Label")
    qtbot.mouseClick(add_button, Qt.LeftButton)
    
    # Select the test label
    for i in range(label_dialog.label_list.count()):
        item = label_dialog.label_list.item(i)
        if "test_label" in item.text():
            label_dialog.label_list.setCurrentItem(item)
            break
    
    # Click remove button
    remove_button = next(btn for btn in label_dialog.findChildren(QPushButton) if btn.text() == "Remove Selected")
    qtbot.mouseClick(remove_button, Qt.LeftButton)
    
    # Check if label was removed
    items = [label_dialog.label_list.item(i).text() for i in range(label_dialog.label_list.count())]
    assert not any("test_label" in item for item in items)

def test_label_dialog_choose_color(label_dialog, monkeypatch, qtbot):
    # Mock QColorDialog.getColor
    test_color = QColor("#FF00FF")
    monkeypatch.setattr('PySide6.QtWidgets.QColorDialog.getColor', lambda *args, **kwargs: test_color)
    
    # Click color button
    color_button = label_dialog.color_button
    qtbot.mouseClick(color_button, Qt.LeftButton)
    
    # Check if color was updated
    assert label_dialog.current_color == test_color
    assert "background-color" in color_button.styleSheet()
