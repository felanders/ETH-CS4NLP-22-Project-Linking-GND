# Setup

`python3 -m venv ./venv`

`source ./venv/bin/activate`

`pip install -r requirements.txt`

Finally, you need to download german fasttext model from fasttext.cc or simply this link: https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.de.300.bin.gz, unpack the .gz and finally run these commands in pyhton:

```from gensim.models.fasttext import FastText, load_facebook_vectors```

```model = load_facebook_vectors("cc.de.300.bin")```

```model.save("./fasttext")```

This takes a while and requires a lot of RAM (16 GB were barely sufficient)

# Notebook

The `linking.ipynb` notebook contains the necessary code. All sections are designed to be self sufficient.

# Data

The data was extracted from the basline system and is to be found in ```data/raw/link```

We saved all the important varialbles for all intermediary steps. Thus you do not have to run all steps e.g. if you do not want to install the german FastText vectors locally...

