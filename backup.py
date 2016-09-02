#!/usr/bin/python

import getpass
import logging
import os
from datetime import datetime
from shutil import copytree, copy2

import tkMessageBox
import tkSimpleDialog
from Tkinter import Tk, Frame, Label, OptionMenu, Checkbutton, StringVar, IntVar, Button
from ttk import Progressbar

logging.basicConfig(level=logging.DEBUG)


class Application(Frame):
    """
    GUI for the backup application.

    Allows user to select the backup drive and the files to backup.
    """

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.errors = False
        self.pack()
        self.createWidgets()

    def createDriveSelector(self):
        """Create the dropdown to select the backup drive."""

        drives = scan_for_drives()
        if not drives:
            drives = ['']
        self.drive_frame = Frame(self)
        drive_label = Label(self.drive_frame, text='Backup Drive')
        self.current_drive = StringVar(self)
        self.current_drive.set(drives[0])
        drive_selector = OptionMenu(self.drive_frame, self.current_drive, *drives)
        drive_selector.config(width=30)

        self.drive_frame.pack()
        drive_label.pack({'side': 'left', 'padx': 10, 'pady': 10})
        drive_selector.pack({'side': 'right', 'padx': 10, 'pady': 10})

    def createCheckboxes(self):
        """Create checkboxes so the user can pick folders to backup."""

        self.directory_frame = Frame(self)
        self.directory_frame.pack()

        options = sorted(scan_home_directory())
        self.checkboxes = {}
        for option in options:
            var = IntVar()
            var.set(1)
            self.checkboxes[option] = var
            cb = Checkbutton(self.directory_frame, text=option, variable=var, anchor='w')
            cb.pack({'padx': 0, 'pady': 5, 'fill': 'both'})

    def createWidgets(self):
        """Create the widgets for the parent frame."""

        self.createDriveSelector()
        self.createCheckboxes()

        self.backup_button = Button(self, text='Backup', command=self.backup)
        self.backup_button.pack({'side': 'bottom', 'padx': 10, 'pady': 10})

        if self.current_drive.get() == '':
            tkMessageBox.showwarning('Error', 'No backup drives detected')

    def backup(self):
        """Backup the selected folders to the selected drive."""

        folders_to_backup = []
        for option in self.checkboxes:
            if self.checkboxes[option].get():
                folders_to_backup.append(option)
        if self.current_drive.get() == '':
            return
        self.drive_frame.pack_forget()
        self.directory_frame.pack_forget()
        self.backup_button.pack_forget()

        self.progress = Progressbar(self, maximum=len(folders_to_backup) + 1, length=300)
        self.progress.pack({'padx': 20, 'pady': 20})
        self.progress_string = StringVar()
        self.progress_string.set('Creating backup folder')
        label = Label(self, textvariable=self.progress_string)
        label.pack({'pady': 20, 'padx': 50})
        self.update()

        perform_backup(self.current_drive.get(), folders_to_backup, self.progress_callback)
        self.progress.pack_forget()
        if self.errors:
            self.progress_string.set('There were errors. Check the backup.')
        else:
            self.progress_string.set('Done (and nothing bad happened)! You can exit now.')

    def progress_callback(self, info, error=None):
        """Callback to update the progress bar and subtext."""

        if error is not None:
            self.errors = True
            tkMessageBox.showwarning(info, error)
            return
        self.progress.step(1)
        self.progress_string.set(info)
        self.update()


def make_backup_folder(destination):
    """Create a backup folder from the username and the current time."""

    username = getpass.getuser()
    if not os.path.exists(destination):
        raise IOError('Destination "{}" does not exist'.format(destination))
    folder_name = '{}_{}'.format(username, datetime.now().strftime('%Y-%m-%dT%H_%M_%S'))
    folder_path = os.path.join(destination, folder_name)
    os.mkdir(folder_path)
    return folder_path


def backup_folders(destination, folders, progress_callback):
    """Backup a list of folders to a destination folder."""

    home = os.path.expanduser('~')
    for folder in folders:
        current_folder = os.path.join(home, folder)
        backup_folder = os.path.join(destination, folder)
        progress_callback('Backing up "{}"'.format(current_folder))
        if not os.path.exists(current_folder):
            msg = 'Folder "{}" does not exist, skipping'.format(current_folder)
            logging.warning(msg)
            progress_callback('Directory DNE', msg)
            return
        try:
            if not os.path.isdir(current_folder):
                copy2(current_folder, backup_folder)
            else:
                copytree(current_folder, backup_folder)
        except:
            msg = 'Failed to copy to "{}"'.format(backup_folder)
            logging.error(msg, exc_info=True)
            progress_callback('Failed to Copy', msg)
            continue
        logging.info('Successfully backed up "{}"'.format(current_folder))
    progress_callback('Done')


def perform_backup(destination, folders, progress_callback):
    """Create a backup folder and copy important directories to the backup."""

    backup_folder = make_backup_folder(destination)
    logging.info('Created backup folder "{}"'.format(backup_folder))
    backup_folders(backup_folder, folders, progress_callback)
    logging.info('Done backing up folders')


def scan_for_drives():
    """Return a list of drives from the /media/user directory."""

    mnt = '/media/{}'.format(getpass.getuser())
    return map(lambda x: os.path.join(mnt, x), os.listdir(mnt))


def scan_home_directory():
    """Return a list of non-hidden files and folders in the home directory."""

    home = os.path.expanduser('~')
    objs = os.listdir(home)
    return filter(lambda x: not x.startswith('.'), objs)


if __name__ == '__main__':
    root = Tk()
    root.title('Backup')
    app = Application(master=root)
    app.mainloop()
