import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import inference_utils as infer
from glob import glob
from argparse import ArgumentParser

import heuristics
from inference_utils import smooth_predictions_with_hmm


def parser():
    ap = ArgumentParser()
    ap.add_argument('--debug_data_path', type=str,
                    help='location of debugging data',
                    required=True)
    ap.add_argument('--sample_rate', type=int, default=48000,
                    help='sample rate of audio recording')
    ap.add_argument('--hop_length', type=int, default=200,
                    help='length of hops b/t subsequent spectrogram windows')
    ap.add_argument('--apply_heuristics', action='store_true',
                    help='whether or not to apply heuristics specified in heuristics.py'
                         'this will run the hmm on the processed predictions'
                         '(this will NOT change results, just visualize them!)')

    return ap.parse_args()


def main(data_root, hop_length, sample_rate, apply_heuristics):

    medians = infer.load_pickle(os.path.join(data_root, 'median_predictions.pkl'))
    medians = np.expand_dims(np.transpose(medians), 0)
    spectrogram = infer.load_pickle(os.path.join(data_root, 'raw_spectrogram.pkl'))

    if not apply_heuristics:

        hmm_predictions = infer.convert_argmaxed_array_to_rgb(infer.load_pickle(os.path.join(data_root, 'hmm_predictions.pkl')))

    prediction_df = infer.load_prediction_csv(os.path.join(data_root, 'classifications.csv'),
                                              hop_length=hop_length,
                                              sample_rate=sample_rate)

    # remove prediction df
    prediction_df = prediction_df.loc[prediction_df['Sound_Type'] != "BACKGROUND", :]

    fig, ax = plt.subplots(sharex=True, nrows=2, figsize=(10, 7))

    iqr = infer.load_pickle(os.path.join(data_root, 'iqrs.pkl'))

    predictions = np.argmax(medians.squeeze(), axis=1)
    if apply_heuristics:
        for heuristic in heuristics.HEURISTIC_FNS:
            predictions = heuristic(predictions, iqr)
        hmm_predictions = infer.convert_argmaxed_array_to_rgb(smooth_predictions_with_hmm(predictions))

    predictions_rgb = infer.convert_argmaxed_array_to_rgb(predictions)
    iqr = np.expand_dims(np.transpose(iqr), 0)

    prediction_array = np.concatenate((hmm_predictions,
                                       predictions_rgb,
                                       iqr,
                                       medians), axis=0)

    # TODO: refactor so I only plot in a window
    # for class_index, name in infer.CLASS_CODE_TO_NAME.items():
    #     subdf = prediction_df.loc[prediction_df['Sound_Type'] == name, :]
    #     ax[0].vlines(subdf['Begin Spect Index'], ymin=0, ymax=spectrogram.shape[0],
    #                  colors=infer.SOUND_TYPE_TO_COLOR[name])
    # for class_index, name in infer.CLASS_CODE_TO_NAME.items():
    #     subdf = prediction_df.loc[prediction_df['Sound_Type'] == name, :]
    #     ax[0].vlines(subdf['End Spect Index'], ymin=0, ymax=spectrogram.shape[0], linestyles='dashed',
    #                  colors=infer.SOUND_TYPE_TO_COLOR[name])

    # for cls in infer.SOUND_TYPE_TO_COLOR.keys():
    #     ax[0].plot([0, 0], [0, spectrogram.shape[0]], '{}-'.format(infer.SOUND_TYPE_TO_COLOR[cls]),
    #                label='begin of {} chirp'.format(cls))
    # for cls in infer.SOUND_TYPE_TO_COLOR.keys():
    #     ax[0].plot([0, 0], [0, spectrogram.shape[0]], '{}-.'.format(infer.SOUND_TYPE_TO_COLOR[cls]),
    #                label='begin of {} chirp'.format(cls))

    ax[1].set_yticks([0, 1, 2, 3])
    ax[1].set_xticks([])
    ax[1].set_xlabel('spectrogram record')
    ax[1].set_yticklabels(['heuristics + smoothing w/ hmm', 'median argmax', 'iqr',
                           'median predictions'], rotation=45)
    ax[1].set_title('Predictions mapped to RGB values. red: A chirp, green: B chirp, blue: background')
    ax[0].set_title('Raw spectrogram')
    ax[0].set_ylabel('frequency bin')

    plt.subplots_adjust(right=0.7)
    axcolor = 'lightgoldenrodyellow'
    axpos = plt.axes([0.2, 0.0001, 0.65, 0.03], facecolor=axcolor)
    spos = Slider(axpos, 'x-position', 0.0, medians.shape[1])

    n = 800
    ax[0].imshow(spectrogram[:, 0:n],
                 aspect='auto')
    ax[1].imshow(prediction_array[:, 0:n],
                 aspect='auto',
                 interpolation='nearest')

    def update(val):
        loc = int(spos.val)
        if loc >= (spectrogram.shape[-1] - n):
            ax[1].imshow(prediction_array[:, loc:-1], aspect='auto', interpolation='nearest')
            ax[0].imshow(spectrogram[:, loc:-1], aspect='auto')
        else:
            ax[1].imshow(prediction_array[:, loc:loc+n], aspect='auto', interpolation='nearest')
            ax[0].imshow(spectrogram[:, loc:loc+n], aspect='auto')
        fig.canvas.draw_idle()

    spos.on_changed(update)
    plt.show()


if __name__ == '__main__':
    args = parser()
    main(args.debug_data_path, args.hop_length, args.sample_rate, args.apply_heuristics)
