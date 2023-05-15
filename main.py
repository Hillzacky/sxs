import gi
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import subprocess
import signal
import shlex

# Fungsi untuk menjalankan proses FFmpeg
def run_ffmpeg_process(input_file, output_url, repeat):
    command = [
        'ffmpeg',
        '-stream_loop', '-1' if repeat else '0',
        '-i', input_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-f', 'flv',
        output_url
    ]
    process = subprocess.Popen(command, preexec_fn=os.setsid)
    return process

# Fungsi untuk menghentikan proses FFmpeg
def stop_ffmpeg_process(process):
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.terminate()
    process.wait()

# Fungsi untuk menangani sinyal SIGINT (Ctrl+C)
def handle_sigint(signal, frame):
    Gtk.main_quit()

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Stream x Server")
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.glade")
        # Menghubungkan sinyal
        self.builder.connect_signals(self)
        # Tangkap sinyal SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, handle_sigint)
        # Mendapatkan objek window utama
        self.main_window = self.builder.get_object("main_window")
        self.main_box = self.builder.get_object("main_box")
        self.add(self.main_box)
        # Mendapatkan objek widget lainnya
        self.input_file_entry = self.builder.get_object("input_file_entry")
        self.output_urls_textview = self.builder.get_object("output_urls_textview")
        self.repeat_checkbox = self.builder.get_object("repeat_checkbox")
        self.start_button = self.builder.get_object("start_button")
        self.stop_button = self.builder.get_object("stop_button")

        self.process = None
        self.processes = []

    def on_start_button_clicked(self, button):
        input_file = self.input_file_entry.get_text()
        output_urls = self.output_urls_textview.get_buffer().get_text(
            self.output_urls_textview.get_buffer().get_start_iter(),
            self.output_urls_textview.get_buffer().get_end_iter(),
            True
        ).splitlines()
        repeat = self.repeat_checkbox.get_active()

        if not os.path.isfile(input_file):
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="File not found",
                secondary_text="The input file does not exist."
            )
            dialog.run()
            dialog.destroy()
            return

        self.processes = []

        for output_url in output_urls:
            output_url = output_url.strip()

            if not output_url:
                continue

            command = [
                'ffmpeg',
                '-stream_loop', '-1' if repeat else '0',
                '-i', input_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-f', 'flv',
                output_url
            ]
            process = subprocess.Popen(shlex.split(' '.join(command)), preexec_fn=os.setsid)
            self.processes.append(process)

        self.start_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)

        GObject.timeout_add(500, self.check_ffmpeg_processes)

    def on_stop_button_clicked(self, button):
        for process in self.processes:
            stop_ffmpeg_process(process)
        self.processes = []
        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)

    def check_ffmpeg_processes(self):
        running_processes = []
        for process in self.processes:
            return_code = process.poll()
            if return_code is None:
                running_processes.append(process)
        self.processes = running_processes

        if len(self.processes) == 0:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            return False

        return True

    def on_main_window_destroy(self, window):
        Gtk.main_quit()

if __name__ == "__main__":
    window = MainWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
