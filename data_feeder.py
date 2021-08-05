from glob import glob
import os
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, OrderedDict
import torch
import random
import spectrogram_analysis as sa

LABEL_TO_INDEX = {'A': 0, 'B': 1, 'X': 2}
INDEX_TO_LABEL = {0: 'A', 1: 'B', 2: 'X'}


class SpectrogramDataset(torch.utils.data.Dataset):

    def __init__(self,
                 dataset_type,
                 spect_type,
                 max_spec_length=40,
                 filtered_sounds=['C', 'Y'],
                 clip_spects=True):
        self.spect_lengths = defaultdict(list)
        self.dataset_type = dataset_type
        self.spect_type = spect_type
        self.max_spec_length = max_spec_length
        self.filtered_sounds = filtered_sounds
        self.clip_spects = clip_spects
        # spectrograms_list[i][0] is the label, [i][1] is the spect.
        self.spectrograms_list, self.unique_labels = self.load_in_all_files(self.dataset_type, self.spect_type,
                                                                            self.filtered_sounds)

    def load_in_all_files(self, dataset_type, spect_type, filtered_labels):
        # saves spectrograms into a list and creates a sorted dictionary (sorted_class_counter) of the counts of each
        # sound class, which is mainly meant for creating the bar chart. also ensures filtering of unwanted labels.
        spectrograms_list = []
        root = os.path.join('data', dataset_type, spect_type, 'spect')
        files = glob(os.path.join(root, "*"))
        class_counter = defaultdict(int)
        for filepath in files:
            head, tail = os.path.split(filepath)
            label = tail.split(".")[0]
            spect = np.load(filepath)
            if label not in filtered_labels and spect.shape[1] >= self.max_spec_length:
                class_counter[label] += 1
                spectrograms_list.append([label, spect])
            self.spect_lengths[label].append(spect.shape[1])
        sorted_class_counter = OrderedDict(sorted(class_counter.items()))
        return spectrograms_list, sorted_class_counter

    def __getitem__(self, idx):
        # returns a tuple with [0] the class label and [1] a slice of the spectrogram or the entire image.
        label = self.spectrograms_list[idx][0]
        spect = self.spectrograms_list[idx][1]
        num_col = spect.shape[1]
        random_index = round(random.uniform(0, num_col - self.max_spec_length))
        # random_index = 0
        if self.clip_spects:
            spect_slice = torch.tensor(spect[:, random_index:random_index + self.max_spec_length])
            label_tensor = torch.tensor(np.repeat(a=LABEL_TO_INDEX[label], repeats=self.max_spec_length))
        else:
            spect_slice = torch.tensor(spect)
            label_tensor = torch.tensor(np.repeat(a=LABEL_TO_INDEX[label], repeats=len(spect[1])))
        return spect_slice, label_tensor

    def __len__(self):
        return len(self.spectrograms_list)

    def generate_bar_chart(self):
        # saves bar chart created from unique_labels dictionary into 'image_offload' directory.
        labels = list(self.unique_labels.keys())
        counts = list(self.unique_labels.values())
        plt.style.use("dark_background")
        plt.bar(labels, counts, color='hotpink')
        plt.title('Bar chart of counts of each class in ' + self.dataset_type)
        plt.savefig('image_offload/' + "bar_chart_" + self.dataset_type + '.png')
        plt.close()

    def generate_lengths_histograms(self, plotted_sound_types=['A','B','X'], plot_all=True):
        # saves histograms of lengths for each plotted_sound_type or every labeled sound into 'image_offload' directory.
        if not (plotted_sound_types or plot_all):
            raise ValueError('No plot requirements given. Designate specific sound types or to plot all types.')

        for sound_type in plotted_sound_types:
            plt.style.use("dark_background")
            plt.hist(self.spect_lengths[sound_type], bins=25, color='lightskyblue')
            plt.title('lengths histogram of ' + sound_type + ' in ' + self.dataset_type)
            plt.show()
            file_title = 'lengths_histogram_' + sound_type + '_' + self.dataset_type + '.png'
            plt.savefig('image_offload/' + file_title)
            print('saved ' + file_title + '.')
            plt.close()

        if plot_all:
            all_lengths = []
            for sound_type, lengths_list in self.spect_lengths.items():
                for length in lengths_list:
                    all_lengths.append(length)
            plt.style.use("dark_background")
            plt.hist(all_lengths, bins=25, color='aquamarine')
            plt.title('histogram, all lengths in ' + self.dataset_type)
            plt.show()
            file_title = 'lengths_histogram_' + 'all_lengths_' + self.dataset_type + '.png'
            plt.savefig('image_offload/' + file_title)
            print('saved ' + file_title)
            plt.close()

    def get_unique_labels(self):
        return self.unique_labels.keys()


if __name__ == '__main__':
    mel = True
    log = True
    n_fft = 1600
    vert_trim = None

    if vert_trim is None:
        vert_trim = sa.determine_default_vert_trim(mel, log, n_fft)

    spect_type = sa.form_spectrogram_type(mel, n_fft, log, vert_trim)

    train_data = SpectrogramDataset(dataset_type="train", spect_type=spect_type, clip_spects=False)
    exit()
    train_data.generate_bar_chart()

    train_data.generate_lengths_histograms()
    test_data = SpectrogramDataset(dataset_type="test", spect_type=spect_type, clip_spects=False)
    test_data.generate_bar_chart()
    test_data.generate_lengths_histograms()
