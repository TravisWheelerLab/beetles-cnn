import pdb
import matplotlib
import matplotlib.pyplot as plt
import torchaudio
import numpy as np
import pandas as pd
import os

np.random.seed(19680801)

from argparse import ArgumentParser
from matplotlib.widgets import SpanSelector


def parser():
    ap = ArgumentParser()
    ap.add_argument('--wav_file', required=True, type=str,
                    help='which .wav file to analyze')
    ap.add_argument('--output_csv_path', required=True, type=str,
                    help='where to save the labels')
    return ap.parse_args()


def add_example(label_list, wav_file, begin_idx, end_idx, sound_type,
                hop_length=None, sample_rate=None):
    begin_time = convert_spectrogram_index_to_seconds(begin_idx,
                                                            hop_length=hop_length,
                                                            sample_rate=sample_rate)
    end_time = convert_spectrogram_index_to_seconds(end_idx,
                                                          hop_length=hop_length,
                                                          sample_rate=sample_rate)
    label_list.append({
        'Begin Time (s)': begin_time,
        'End Time (s)': end_time,
        'Sound_Type': sound_type.upper(),
        'Filename': wav_file
    })


def load_wav_file(wav_filename):
    waveform, sample_rate = torchaudio.load(wav_filename)
    return waveform, sample_rate


def convert_spectrogram_index_to_seconds(spect_idx, hop_length, sample_rate):
    seconds_per_hop = hop_length / sample_rate
    return spect_idx * seconds_per_hop


class SimpleLabeler:

    def __init__(self, wav_file, output_csv_path):

        self.wav_file = wav_file
        self.output_csv_path = output_csv_path
        self.waveform, self.sample_rate = load_wav_file(self.wav_file)

        self.hop_length = 200

        self.spectrogram = torchaudio.transforms.MelSpectrogram(sample_rate=self.sample_rate,
                                                                n_fft=800,
                                                                hop_length=self.hop_length,
                                                                )(self.waveform).log2().numpy().squeeze()
        self.spectrogram = self.spectrogram[20:, :]

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, figsize=(8, 6))

        self.n = 0
        self.xmin = 0
        self.xmax = 0
        self.interval = 400
        self.label_list = []

        self.ax1.imshow(self.spectrogram[:, self.n:self.n + self.interval])

        self.ax1.set_title('Press left mouse button and drag '
                           'to select a region in the top graph '
                           '0 percent through spectrogram')

        textstr = 'keys control which label is\n' \
                  'assigned to the selected region.\n' \
                  'first navigate with <f,d,j> over\n' \
                  'the spectrogram, then click and\n' \
                  'drag to select a region.\n' \
                  'The selected region will appear\n' \
                  'on the bottom plot. If it looks good,\n' \
                  'save it with <y,w,e>.\n' \
                  'Closing the window will save the labels.\n ' \
                  'key:\n' \
                  'y: save A chirp\n' \
                  'w: save B chirp\n' \
                  'e: save background\n' \
                  'r: delete last label\n' \
                  'a: widen window\n' \
                  't: tighten window\n' \
                  'f: move window right\n' \
                  'd: move window left\n' \
                  'j: jump 10 windows forward\n\n' \
                  'disclaimer: this is not production\n' \
                  'code and has severe limitations\n' \
                  'but should work in certain scenarios.'

        plt.figtext(0.02, 0.25, textstr, fontsize=8)
        plt.subplots_adjust(left=0.25)

        self.fig.canvas.mpl_connect('key_press_event', self.process_keystroke)

        self.span = SpanSelector(self.ax1, self.onselect, 'horizontal', useblit=True,
                                 rectprops=dict(alpha=0.5, facecolor='tab:blue'))
        self._redraw_ax1()

    def show(self):
        self.fig.canvas.draw()
        plt.show()

    def save_labels(self):

        label_df = pd.DataFrame.from_dict(self.label_list)
        if os.path.isfile(self.output_csv_path):
            label_df.to_csv(self.output_csv_path, index=False, mode='a', header=False)
        else:
            label_df.to_csv(self.output_csv_path, index=False, mode='w')

    def _redraw_ax2(self):
        self.ax2.imshow(self.spectrogram[:, self.n + self.xmin: self.n + self.xmax])
        self.ax2.set_title('selected region')
        self.fig.canvas.draw()

    def _redraw_ax1(self):
        # could be
        self.ax1.clear()
        self.ax1.imshow(self.spectrogram[:, self.n:self.n + self.interval], aspect='auto')
        self.ax1.set_title('Press left mouse button and drag '
                           'to select a region in the top graph '
                           '{:d} percent through spectrogram'.format(int(100 * self.n / self.spectrogram.shape[-1])))
        self.fig.canvas.draw()

    def onselect(self, x_min, x_max):
        self.xmin = int(x_min)
        self.xmax = int(x_max)
        if (self.xmax - self.xmin) >= 2:
            self._redraw_ax2()

    def process_keystroke(self, key):

        if key.key in ('y', 'Y'):
            print('saving A chirp (r to delete)')
            add_example(self.label_list,
                        self.wav_file,
                        self.n + self.xmin,
                        self.n + self.xmax, 'A',
                        hop_length=self.hop_length,
                        sample_rate=self.sample_rate)
        elif key.key in ('w', 'W'):
            print('saving B chirp (r to delete)')
            add_example(self.label_list,
                        self.wav_file,
                        self.n + self.xmin,
                        self.n + self.xmax, 'B',
                        hop_length=self.hop_length,
                        sample_rate=self.sample_rate)
        elif key.key in ('e', 'E'):
            add_example(self.label_list,
                        self.wav_file,
                        self.n + self.xmin,
                        self.n + self.xmax, 'background',
                        hop_length=self.hop_length,
                        sample_rate=self.sample_rate)
            print('saving background chirp (r to delete)')
        elif key.key in ('r', 'R'):
            if len(self.label_list):
                self.label_list.pop()
                print('deleting last selection')
            else:
                print('empty label list! hit <A, B, X> after selecting a region'
                      ' to add a labeled region to the list')
        elif key.key in ('a', 'A'):
            print('widening window')
            self.interval += 10
            self._redraw_ax1()
        elif key.key in ('t', 'T'):
            print('tightening window')
            self.interval -= 10
            self._redraw_ax1()
        elif key.key in ('f', 'F'):
            self.n = self.n + self.interval // 2  # could be briefer but this is very clear
            self._redraw_ax1()
        elif key.key in ('j', 'J'):
            self.n = self.n + 10 * self.interval
            self._redraw_ax1()
        elif key.key in ('d', 'D'):
            print('reversing window')
            self.n = self.n - self.interval // 2
            self._redraw_ax1()
        else:
            print("unknown value: hit one of a, b, x")


if __name__ == '__main__':
    args = parser()

    # fix outputs to make them in the same format as the existing data

    labeler = SimpleLabeler(args.wav_file, args.output_csv_path)
    labeler.show()
    labeler.save_labels()
