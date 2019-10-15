#!/usr/bin/python3
# -*- coding: utf-8 -*-

import shutil
from tempfile import NamedTemporaryFile

from PySide2.QtCore import QThreadPool, Qt
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QDoubleSpinBox, QFileDialog, QProgressBar, QMessageBox, \
    QListWidget, QSplitter, QWidget
from pyffi.formats.nif import *

from src.pyqt import QuickyGui
from src.pyqt.MainWindow import MainWindow
from src.pyqt.Worker import Worker
from src.utils.config import CONFIG, save_config

log = logging.getLogger(__name__)


class NifBatchTools(MainWindow):

    def __init__(self):
        super().__init__("HTools - NifBatchTools")
        log.info("Opening NifBatchTools window")

        self.thread_pool = QThreadPool()
        self.source_folder = CONFIG.get("DEFAULT", "SourceFolder")
        self.destination_folder = CONFIG.get("DEFAULT", "DestinationFolder")
        self.keywords = list(map(lambda x: x.encode("ascii"), CONFIG.get("NIF", "keywords").replace(" ", "").split(",")))
        self.nif_files = set()

        log.info("Source folder  : " + self.source_folder)
        log.info("Keywords       : " + str(self.keywords))

        self.init_ui()

    def update_nif_files(self, value=0):
        self.lcd_nif_files_loaded.display(str(len(self.nif_files)))
        self.nif_files_list_widget.clear()
        self.nif_files_list_widget.addItems(list(self.nif_files))

    def init_ui(self):
        main_splitter = QSplitter(self, Qt.Horizontal)

        left_pane = QWidget(self)
        left_pane.setMaximumWidth(370)
        left_v_box = QVBoxLayout(self)
        left_pane.setLayout(left_v_box)

        right_pane = QWidget(self)
        right_v_box = QVBoxLayout(self)
        right_pane.setLayout(right_v_box)

        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(right_pane)

        # ===== Details =====
        self.group_box_details = QuickyGui.create_group_box(self, "Details")

        nif_files_loaded = QuickyGui.create_label(self, ".nif files loaded")
        self.lcd_nif_files_loaded = QuickyGui.create_lcd(self)

        vbox = QVBoxLayout(self)

        hbox = QHBoxLayout(self)
        hbox.addWidget(nif_files_loaded)
        hbox.addWidget(self.lcd_nif_files_loaded)

        self.nif_files_list_widget = QListWidget()
        self.update_nif_files()

        vbox.addItem(hbox)
        vbox.addWidget(self.nif_files_list_widget)

        self.group_box_details.setLayout(vbox)
        right_v_box.addWidget(self.group_box_details)

        # ===== STEP 0 - Instructions =====
        self.group_box_instructions = QuickyGui.create_group_box(self, "Instructions")

        instructions = QuickyGui.create_label(self, "By clicking on \"Scan Folder\", all .nif contained in this folder (subfolders and so on), will be added to the list of files to process. You can scan multiple folder, by clicking again. All files not already present will be added.")

        vbox = QVBoxLayout()
        vbox.addWidget(instructions)

        self.group_box_instructions.setLayout(vbox)
        left_v_box.addWidget(self.group_box_instructions)

        # ===== STEP I - Load Files =====
        self.group_box_load_files = QuickyGui.create_group_box(self, "STEP I - Load .nif files")

        button_load_files = QuickyGui.create_button(self, "Scan Folder", self.action_load_files)
        button_clear_files = QuickyGui.create_button(self, "Clear loaded files", self.action_clear_files)

        hbox = QHBoxLayout()
        hbox.addWidget(button_load_files)
        hbox.addWidget(button_clear_files)

        self.group_box_load_files.setLayout(hbox)
        left_v_box.addWidget(self.group_box_load_files)

        # ===== STEP II - Set parameters =====
        self.group_box_parameters = QuickyGui.create_group_box(self, "STEP II - Set parameters")

        vbox = QVBoxLayout()

        # Glossiness
        label_glossiness = QuickyGui.create_label(self, "Glossiness")
        self.spin_box_glossiness = QDoubleSpinBox()
        self.spin_box_glossiness.setMinimum(0)
        self.spin_box_glossiness.setMaximum(1000)
        self.spin_box_glossiness.setValue(CONFIG.getfloat("NIF", "Glossiness"))
        log.info("Glossiness target : " + str(self.spin_box_glossiness.value()))

        hbox = QHBoxLayout()
        hbox.addWidget(label_glossiness)
        hbox.addWidget(self.spin_box_glossiness)
        vbox.addItem(hbox)

        # Specular Strength
        label_specular_strength = QuickyGui.create_label(self, "Specular Strength")
        self.spin_box_specular_strength = QDoubleSpinBox()
        self.spin_box_specular_strength.setMinimum(0)
        self.spin_box_specular_strength.setMaximum(1000)
        self.spin_box_specular_strength.setValue(CONFIG.getfloat("NIF", "SpecularStrength"))
        log.info("Specular Strength target : " + str(self.spin_box_specular_strength.value()))

        hbox = QHBoxLayout()
        hbox.addWidget(label_specular_strength)
        hbox.addWidget(self.spin_box_specular_strength)
        vbox.addItem(hbox)

        self.group_box_parameters.setLayout(vbox)
        left_v_box.addWidget(self.group_box_parameters)

        # ===== STEP III - Apply =====
        self.group_box_apply = QuickyGui.create_group_box(self, "STEP III - Apply")

        button_load_files = QuickyGui.create_button(self, "Apply", self.action_apply)

        hbox = QHBoxLayout()
        hbox.addWidget(button_load_files)

        self.group_box_apply.setLayout(hbox)
        left_v_box.addWidget(self.group_box_apply)

        # ===== Finalizing =====
        self.progress_bar = QProgressBar(self)
        left_v_box.addWidget(self.progress_bar)

        left_v_box.setSpacing(10)
        self.mainLayout.addWidget(main_splitter)

    def toggle(self, value):
        self.group_box_parameters.setEnabled(value)
        self.group_box_load_files.setEnabled(value)
        self.group_box_apply.setEnabled(value)

    def progress(self, value):
        self.progress_bar.setValue(value)

    def finish_action(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self.nif_files))
        self.progress_bar.setValue(len(self.nif_files))
        self.toggle(True)
        log.info("Done !")
        QMessageBox.information(self, "Results", "Done !")

    def action_clear_files(self):
        log.info("Clearing loaded .nif files ...")
        self.nif_files.clear()
        self.update_nif_files()
        self.progress_bar.reset()

    def action_load_files(self):
        log.info("Loading .nif files ...")
        self.toggle(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.ShowDirsOnly)
        file_dialog.setDirectory(self.source_folder)

        if file_dialog.exec_():
            scan_dirs = file_dialog.selectedFiles()
            if len(scan_dirs) >= 1 :
                self.source_folder = scan_dirs[0]
            else:
                self.source_folder = file_dialog.directory()

        worker = Worker(self.load_files)
        worker.signals.finished.connect(self.finish_action)
        worker.signals.progress.connect(self.update_nif_files)

        self.thread_pool.start(worker)

    def load_files(self, progress_callback):
        """
        Traverse folder to find .nif files
        """
        if self.source_folder:
            log.info("Scanning directory : " + self.source_folder)
            CONFIG.set("DEFAULT", "SourceFolder", self.source_folder),
            save_config()

            for root, dirs, files in os.walk(self.source_folder):
                for file in files:
                    if file.endswith(".nif"):
                        self.nif_files.add(root + "/" + file)
                        progress_callback.emit(len(self.nif_files))
        return

    def action_apply(self):
        """
        Apply parameters to relevant .nif files
        """
        if len(self.nif_files) == 0:
            QMessageBox.warning(self, "No .nif files loaded", "Don't forget to load .nif files !")
            return

        log.info("Applying parameters to " + str(len(self.nif_files)) + " files ...")
        self.toggle(False)
        self.progress_bar.setValue(0)

        CONFIG.set("NIF", "Glossiness", str(self.spin_box_glossiness.value())),
        CONFIG.set("NIF", "SpecularStrength", str(self.spin_box_specular_strength.value())),
        save_config()

        worker = Worker(self.apply)
        worker.signals.finished.connect(self.finish_action)
        worker.signals.progress.connect(self.progress)

        self.thread_pool.start(worker)

    def apply(self, progress_callback):
        for counter in range(0, self.nif_files_list_widget.count()):

            item = self.nif_files_list_widget.item(counter)
            item.setForeground(Qt.blue)
            log.info("[" + str(counter) + "] working on : " + item.text())

            result = self.process_nif_files(item.text())

            if result:
                item.setForeground(Qt.darkGreen)
            else:
                item.setForeground(Qt.darkRed)

            progress_callback.emit(counter + 1)
        return

    def process_nif_files(self, path):
        file_name = path.rsplit("/", 1)[1]

        success = False
        with open(path, 'rb') as stream:
            data = NifFormat.Data()
            data.read(stream)
            root = data.roots[0]

            # First, let's get relevant NiTriShape block
            block = None
            index = 0
            while not block and index < len(self.keywords):
                block = root.find(self.keywords[index])
                index += 1

            # Second, if found, change its parameters
            if block is not None:
                for subblock in block.tree():
                    if subblock.__class__.__name__ == "BSLightingShaderProperty":
                        old_gloss = subblock.glossiness
                        subblock.glossiness = self.spin_box_glossiness.value()
                        old_spec_strength = subblock.specular_strength
                        subblock.specular_strength = self.spin_box_specular_strength.value()
                        log.info("        Glossiness " + str(old_gloss) + " -> " + str(self.spin_box_glossiness.value()) + " | Specular Strength " + str(old_spec_strength) + " -> " + str(self.spin_box_specular_strength.value()))
                        success = True

        if success:
            # Finaly, save changes
            f = NamedTemporaryFile(mode='wb', delete=False)
            tmp_file_name = f.name
            data.write(f)
            f.close()
            shutil.copy(tmp_file_name, path)
            os.remove(tmp_file_name)

        return success
