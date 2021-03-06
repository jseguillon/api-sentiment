from sequence_tagging.config_seq import Config
from sequence_tagging.model.data_utils import CoNLLDataset, get_vocabs, UNK, NUM, \
     write_vocab, load_vocab, get_char_vocab, \
    export_trimmed_fasttext_vectors, get_processing_word
#import spacy
#fr_nlp= spacy.load("fr")

def main():
    """Procedure to build data

    You MUST RUN this procedure. It iterates over the whole dataset (train,
    dev and test) and extract the vocabularies in terms of words, tags, and
    characters. Having built the vocabularies it writes them in a file. The
    writing of vocabulary in a file assigns an id (the line #) to each word.
    It then extract the relevant GloVe vectors and stores them in a np array
    such that the i-th entry corresponds to the i-th word in the vocabulary.


    Args:
        config: (instance of Config) has attributes like hyper-params...

    """
    # get config and processing of words
    config = Config()
    FLAGS=config.get_flags(".",load=False)
    processing_word = get_processing_word(lowercase=True)

    # Generators
    dev   = CoNLLDataset(FLAGS.filename_dev, processing_word)
    test  = CoNLLDataset(FLAGS.filename_test, processing_word)
    train = CoNLLDataset(FLAGS.filename_train, processing_word)

    # Build Word and Tag vocab
    vocab_words, vocab_tags = get_vocabs([train, dev, test])
    #vocab_glove = get_glove_vocab(config.filename_glove)

    vocab = vocab_words
            #& vocab_glove
    vocab.add(UNK)
    vocab.add(NUM)

    # Save vocab
    write_vocab(vocab, FLAGS.filename_words)
    write_vocab(vocab_tags, FLAGS.filename_tags)

    # Trim GloVe Vectors
    vocab = load_vocab(FLAGS.filename_words)
    #export_trimmed_glove_vectors(vocab, config.filename_glove,
     #                           config.filename_trimmed, config.dim_word)
    export_trimmed_fasttext_vectors(vocab, FLAGS.filename_trimmed, config.dim_word)

    # Build and save char vocab
    train = CoNLLDataset(FLAGS.filename_train)
    vocab_chars = get_char_vocab(train)
    write_vocab(vocab_chars, FLAGS.filename_chars)


if __name__ == "__main__":
    main()
