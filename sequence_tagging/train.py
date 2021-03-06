from sequence_tagging.model.data_utils import CoNLLDataset
from sequence_tagging.model.ner_model import NERModel
from sequence_tagging.config_seq import Config


def main():
    # create instance of config
    config = Config()
    FLAGS=config.get_flags(".")
    # build model
    model = NERModel(config,FLAGS)
    model.build()
    # model.restore_session("results/crf/model.weights/") # optional, restore weights
    # model.reinitialize_weights("proj")

    # create datasets
    dev   = CoNLLDataset(FLAGS.filename_dev, config.processing_word, config.processing_tag, FLAGS.max_iter)
    train = CoNLLDataset(FLAGS.filename_train, config.processing_word, config.processing_tag, FLAGS.max_iter)

    # train model
    model.train(train, dev)

if __name__ == "__main__":
    main()
