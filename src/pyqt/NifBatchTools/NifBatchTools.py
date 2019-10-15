#!/usr/bin/python3
# -*- coding: utf-8 -*-

import shutil
import itertools
from tempfile import NamedTemporaryFile
from PySide2.QtCore import QThreadPool, Qt, QSize, QThread
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QDoubleSpinBox, QFileDialog, QProgressBar, QMessageBox, \
    QListWidget, QSplitter, QWidget, QListWidgetItem, QApplication
from pyffi.formats.nif import *
from src.pyqt import QuickyGui
from src.pyqt.MainWindow import MainWindow
from src.pyqt.Worker import Worker
from src.utils.config import CONFIG, save_config
from src.utils.misc import chunkify

log = logging.getLogger(__name__)


class NifBatchTools(MainWindow):

    def __init__(self):
        super().__init__("HTools - NifBatchTools")
        log.info("Opening NifBatchTools window")

        self.source_folder = CONFIG.get("DEFAULT", "SourceFolder")
        self.destination_folder = CONFIG.get("DEFAULT", "DestinationFolder")
        self.keywords = list(map(lambda x: x.encode("ascii"), CONFIG.get("NIF", "keywords").replace(" ", "").split(",")))
        self.nif_files = set() # improve performance (better to check in a set rather than in a QListWidget
        self.ignored_nif_files = set() # improve performance (better to check in a set rather than in a QListWidget
        self.setSize(QSize(700, 600))
        self.processed_files = itertools.count()

        log.info("Source folder  : " + self.source_folder)
        log.info("Keywords       : " + str(self.keywords))

        self.init_ui()

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

        nif_files_ignored = QuickyGui.create_label(self, ".nif files ignored")
        self.lcd_nif_files_ignored = QuickyGui.create_lcd(self)


        self.nif_files_list_widget = QListWidget()
        self.nif_files_list_widget.setAlternatingRowColors(True)
        self.nif_files_list_widget.setStyleSheet("QListWidget {padding: 10px;} QListWidget::item { margin: 10px; }")
        self.nif_files_list_widget.itemDoubleClicked.connect(self.open_file_location)

        self.ignored_nif_files_list_widget = QListWidget()
        self.ignored_nif_files_list_widget.setAlternatingRowColors(True)
        self.ignored_nif_files_list_widget.setStyleSheet("QListWidget {padding: 10px;} QListWidget::item { margin: 10px}")
        self.ignored_nif_files_list_widget.itemDoubleClicked.connect(self.open_file_location)
        self.update_nif_files()

        self.group_box_legends = QuickyGui.create_group_box(self, "Legends")
        instructions_4 = QuickyGui.create_label(self, "Green - File correctly processed\n")
        instructions_4.setStyleSheet("QLabel { color : darkGreen; font-weight : bold }")
        instructions_5 = QuickyGui.create_label(self, "Blue - File is processing\n")
        instructions_5.setStyleSheet("QLabel { color : darkBlue; font-weight : bold }")
        instructions_6 = QuickyGui.create_label(self, "Red - File ignored.")
        instructions_6.setStyleSheet("QLabel { color : darkRed; font-weight : bold }")
        instructions_7 = QuickyGui.create_label(self, "Reason : Couldn't find a NiTriShape block whose name is specified in provided keywords. It may be normal, if there is no body part. But if there is and you want this file to be processed by the tool, then you must add the corresponding NiTriShape block's name (use nikskope to find it) to the list of keywords, located in the .ini file, situated alongside the executable."
                                                      " If you have Nikskope, you can open the file by double-clicking on in, in the list view, or from your explorer. Restart the tool to load the new .ini file.")
        instructions_7.setStyleSheet("QLabel { color : darkRed}")

        vbox = QVBoxLayout()
        vbox.setSpacing(5)
        vbox.addWidget(instructions_4)
        vbox.addWidget(instructions_5)
        vbox.addWidget(instructions_6)
        vbox.addWidget(instructions_7)

        self.group_box_legends.setLayout(vbox)

        vbox = QVBoxLayout(self)

        hbox = QHBoxLayout(self)
        hbox.addWidget(nif_files_loaded)
        hbox.addWidget(self.lcd_nif_files_loaded)

        vbox.addItem(hbox)
        vbox.addWidget(self.nif_files_list_widget)

        hbox = QHBoxLayout(self)
        hbox.addWidget(nif_files_ignored)
        hbox.addWidget(self.lcd_nif_files_ignored)
        vbox.addItem(hbox)

        vbox.addWidget(self.ignored_nif_files_list_widget)
        vbox.addWidget(self.group_box_legends)

        self.group_box_details.setLayout(vbox)
        right_v_box.addWidget(self.group_box_details)

        # ===== STEP 0 - Instructions =====
        self.group_box_instructions = QuickyGui.create_group_box(self, "Instructions")

        instructions_1 = QuickyGui.create_label(self, "I. By clicking on \"Scan Folder\", all .nif contained in this folder (subfolders and so on), will be added to the set of files to be processed. You can scan multiple folder, by clicking again. All files not already present will be added.")
        instructions_2 = QuickyGui.create_label(self, "II. Once your desired parameters are set, click on \"Apply\". Bewary, the process is quite slow (just opening the file is quite consuming somehow)")

        vbox = QVBoxLayout()
        vbox.setSpacing(5)
        vbox.addWidget(instructions_1)
        vbox.addWidget(instructions_2)

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

    def open_file_location(self, item):
        os.startfile(item.text(), 'open')

    def toggle(self, value):
        self.group_box_parameters.setEnabled(value)
        self.group_box_load_files.setEnabled(value)
        self.group_box_apply.setEnabled(value)

    def progress(self, value):
        self.progress_bar.setValue(value+1)

    def update_nif_files(self, value=0):
        self.lcd_nif_files_loaded.display(self.nif_files_list_widget.count())
        self.lcd_nif_files_ignored.display(self.ignored_nif_files_list_widget.count())

    def finish_action(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(max(1, self.nif_files_list_widget.count()))
        self.progress_bar.setValue(self.nif_files_list_widget.count())
        self.toggle(True)
        log.info("Done !")

    def finish_load_action(self, result):
        self.finish_action()
        QMessageBox.information(self, "Results", "Done !\n\n" + str(self.nif_files_list_widget.count()) + " .nif file(s) loaded.\n" + str(result) + " .nif files ignored.")

    def finish_apply_action(self):
        if QThreadPool.globalInstance().activeThreadCount() == 0:
            self.finish_action()
            QMessageBox.information(self, "Results", "Done !\n\n" + str(self.progress_bar.value()) + " .nif file(s) loaded.\n")

    def action_clear_files(self):
        log.info("Clearing loaded .nif files ...")
        self.nif_files_list_widget.clear()
        self.ignored_nif_files_list_widget.clear()
        self.nif_files.clear()
        self.ignored_nif_files.clear()
        self.update_nif_files()
        self.progress_bar.reset()

    def action_load_files(self):
        log.info("Loading .nif files ...")
        self.toggle(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setDirectory(self.source_folder)

        if file_dialog.exec_():
            scan_dirs = file_dialog.selectedFiles()
            if len(scan_dirs) >= 1 :
                self.source_folder = scan_dirs[0]
            else:
                self.source_folder = file_dialog.directory()

        if self.source_folder:
            log.info("Scanning directory : " + self.source_folder)
            CONFIG.set("DEFAULT", "SourceFolder", self.source_folder),
            save_config()

        worker = Worker(self.load_files)
        worker.signals.result.connect(self.finish_load_action)
        worker.signals.progress.connect(self.update_nif_files)

        QThreadPool.globalInstance().start(worker)

    def load_files(self, progress_callback):
        """
        Traverse folder to find .nif files
        """
        ignored_files = 0
        for root, dirs, files in os.walk(self.source_folder):
            for file in files:
                path = root + "/" + file
                if file.endswith(".nif") and path not in self.nif_files and path not in self.ignored_nif_files:
                    stream = open(path, "rb")
                    data = NifFormat.Data()
                    try:
                        data.inspect(stream)
                        if "NiNode".encode('ascii') == data.header.block_types[0] and any(keyword in self.keywords for keyword in data.header.strings):
                            self.nif_files.add(path)
                            self.nif_files_list_widget.addItem(path)
                        else:
                            item = QListWidgetItem(path, self.ignored_nif_files_list_widget)
                            item.setForeground(Qt.darkRed)
                            ignored_files += 1
                    except ValueError:
                        log.exception("[" + file + "] - Too Big to inspect - skipping")
                    progress_callback.emit(0) # emit parameter is not used
        return ignored_files

    def action_apply(self):
        """
        Apply parameters to relevant .nif files
        """
        if self.nif_files_list_widget.count() == 0:
            QMessageBox.warning(self, "No .nif files loaded", "Don't forget to load .nif files !")
            return

        log.info("Applying parameters to " + str(self.nif_files_list_widget.count()) + " files ...")
        self.toggle(False)
        self.progress_bar.setValue(0)
        self.processed_files = itertools.count()

        CONFIG.set("NIF", "Glossiness", str(self.spin_box_glossiness.value())),
        CONFIG.set("NIF", "SpecularStrength", str(self.spin_box_specular_strength.value())),
        save_config()

        for indices in chunkify(range(self.nif_files_list_widget.count()), max(QThreadPool.globalInstance().maxThreadCount(), 3)):
            worker = Worker(self.apply, indices=indices)
            worker.signals.finished.connect(self.finish_apply_action)
            worker.signals.progress.connect(self.progress)

            QThreadPool.globalInstance().start(worker)
        log.info("Done assigning tasks")

    def apply(self, progress_callback, indices):
        for counter in indices:
            item = self.nif_files_list_widget.item(counter)
            item.setForeground(Qt.blue)
            log.info("[" + str(counter) + "] working on : " + item.text())

            if self.process_nif_files(item.text(), counter):
                item.setForeground(Qt.darkGreen)
                progress_callback.emit(next(self.processed_files))
            else:
                item.setForeground(Qt.darkRed)

    def process_nif_files(self, path, counter):
        file_name = path.rsplit("/", 1)[1]

        success = True
        with open(path, 'rb') as stream:
            data = NifFormat.Data()
            try:
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
                            log.info("[" + str(counter) + "] ------ Glossiness " + str(old_gloss) + " -> " + str(self.spin_box_glossiness.value()) + " | Specular Strength " + str(old_spec_strength) + " -> " + str(self.spin_box_specular_strength.value()))
                            success = True
            except Exception:
                log.exception("Error while reading stream from file : " + path)

        if success:
            # Finally, save changes
            f = NamedTemporaryFile(mode='wb', delete=False)
            tmp_file_name = f.name
            data.write(f)
            f.close()
            shutil.copy(tmp_file_name, path)
            os.remove(tmp_file_name)

        return success
