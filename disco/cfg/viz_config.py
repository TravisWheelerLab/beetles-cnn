from disco.cfg import viz_experiment


@viz_experiment.config
def config():
    data_path = "/Users/wheelerlab/share/disco/disco/resources/example-viz"
    medians = True
    post_process = True
    means = False
    iqr = False
    votes = False
    votes_line = False
    second_data_path = None
