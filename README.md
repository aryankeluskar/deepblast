# TM-Vec

Learning protein structural similarity from sequence alone.  Our preprints can be found [here](https://www.biorxiv.org/content/10.1101/2022.07.25.501437v1) and [here](https://www.biorxiv.org/content/10.1101/2020.11.03.365932v1)

# Installation

TM-Vec can be installed from pip via

```
pip install tm-vec
```

To install from the development branch run

```
pip install git+https://github.com/flatironinstitute/tm-vec.git
```

# Downloading pretrained models and data

The pretrained TM-vec model can be downloaded [here](https://users.flatironinstitute.org/jmorton/public_www/deepblast-public-data/checkpoints/deepblast-lstm4x.pt).

The TM-align structural alignments used to pretrain Tm_Vec_Align can be found [here](https://users.flatironinstitute.org/jmorton/public_www/deepblast-public-data/tmalign.tar.gz)


See the [Malisam](http://prodata.swmed.edu/malisam/) and [Malidup](http://prodata.swmed.edu/malidup/) websites to download their datasets.



# Getting started

We have 2 command line scripts available, namely `tmvec-align-train` and `tmvec-align-eval`.

## Pretraining

`tm_vec_align-train` takes in as input a tab-delimited format of with columns
`query_seq_id | key_seq_id | tm_score1 | tm_score2 | rmsd | sequence1 | sequence2 | alignment_string`
See an example [here](https://raw.githubusercontent.com/flatironinstitute/tm_vec_align/master/data/tm_align_output_10k.tab) of what this looks like. At this moment, we only support parsing the output of TM-align. The parsing script can be found under

`tm_vec_align/dataset/parse_tm_align.py [fname] [output_table]`

Once the data is configured and split appropriately, `tm_vec_align-train` can be run.
The command-line options are given below (see `tm_vec_align-train --help` for more details).

```
usage: tmvec-align-train [-h] [--gpus GPUS] [--grad-accum GRAD_ACCUM] [--grad-clip GRAD_CLIP] [--nodes NODES] [--num-workers NUM_WORKERS] [--precision PRECISION] [--backend BACKEND]
                       [--load-from-checkpoint LOAD_FROM_CHECKPOINT] --train-pairs TRAIN_PAIRS --test-pairs TEST_PAIRS --valid-pairs VALID_PAIRS [--embedding-dim EMBEDDING_DIM]
                       [--rnn-input-dim RNN_INPUT_DIM] [--rnn-dim RNN_DIM] [--layers LAYERS] [--loss LOSS] [--learning-rate LEARNING_RATE] [--batch-size BATCH_SIZE]
                       [--multitask MULTITASK] [--finetune FINETUNE] [--mask-gaps MASK_GAPS] [--scheduler SCHEDULER] [--epochs EPOCHS]
                       [--visualization-fraction VISUALIZATION_FRACTION] -o OUTPUT_DIRECTORY
```

## Evaluation

This will evaluate how much the tm_vec_align predictions agree with the structural alignments.
The `tm_vec_align-train` command will automatically evaluate the heldout test set if it completes.
However, a separate `tm_vec_align-evaluate` command is available in case the pretraining was interrupted.  The commandline options are given below (see `tm_vec_align-evaluate --help` for more details)

```
usage: tmvec-align-evaluate [-h] [--gpus GPUS] [--num-workers NUM_WORKERS] [--nodes NODES] [--load-from-checkpoint LOAD_FROM_CHECKPOINT] [--precision PRECISION] [--backend BACKEND]
                          --train-pairs TRAIN_PAIRS --test-pairs TEST_PAIRS --valid-pairs VALID_PAIRS [--embedding-dim EMBEDDING_DIM] [--rnn-input-dim RNN_INPUT_DIM]
                          [--rnn-dim RNN_DIM] [--layers LAYERS] [--loss LOSS] [--learning-rate LEARNING_RATE] [--batch-size BATCH_SIZE] [--multitask MULTITASK]
                          [--finetune FINETUNE] [--mask-gaps MASK_GAPS] [--scheduler SCHEDULER] [--epochs EPOCHS] [--visualization-fraction VISUALIZATION_FRACTION] -o
                          OUTPUT_DIRECTORY
```


## Loading the models

```python

import torch
from tm_vec_align.trainer import LightningAligner
from tm_vec_align.dataset.utils import pack_sequences
from tm_vec_align.dataset.utils import states2alignment
import matplotlib.pyplot as plt
import seaborn as sns

# Load the pretrained model
model = LightningAligner.load_from_checkpoint(your_model_path)

# Load on GPU (if you want)
model = model.cuda()

# Obtain hard alignment from the raw sequences
x = 'IGKEEIQQRLAQFVDHWKELKQLAAARGQRLEESLEYQQFVANVEEEEAWINEKMTLVASED'
y = 'QQNKELNFKLREKQNEIFELKKIAETLRSKLEKYVDITKKLEDQNLNLQIKISDLEKKLSDA'
pred_alignment = model.align(x, y)
x_aligned, y_aligned = states2alignment(pred_alignment, x, y)
print(x_aligned)
print(pred_alignment)
print(y_aligned)

x_ = torch.Tensor(model.tokenizer(str.encode(x))).long()
y_ = torch.Tensor(model.tokenizer(str.encode(y))).long()

# Pack sequences for easier parallelization
seq, order = pack_sequences([x_], [y_])
seq = seq.cuda()

# Generate alignment score
score = model.aligner.score(seq, order).item()
print('Score', score)

# Predict expected alignment
A, match_scores, gap_scores = model.forward(seq, order)

# Display the expected alignment
fig, ax = plt.subplots(1, 3, figsize=(9, 3))
sns.heatmap(A.cpu().detach().numpy().squeeze(), ax=ax[0], cbar=False,  cmap='viridis')
sns.heatmap(match_scores.cpu().detach().numpy().squeeze(), ax=ax[1],  cmap='viridis')
sns.heatmap(gap_scores.cpu().detach().numpy().squeeze(), ax=ax[2],  cmap='viridis')
ax[0].set_title('Predicted Alignment')
ax[1].set_title('Match scores ($\mu$)')
ax[2].set_title('Gap scores ($g$)')
plt.tight_layout()
plt.show()
```

The output will look like
```
IGKEEIQQRLAQFVDHWKELKQLAAARGQRLEESLEYQQFVANVEEEEAWINEKMTLVASED
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
QQNKELNFKLREKQNEIFELKKIAETLRSKLEKYVDITKKLEDQNLNLQIKISDLEKKLSDA

Score 282.3163757324219
```

![](https://raw.githubusercontent.com/flatironinstitute/tm-vec/master/imgs/example-alignment.png "example alignment")

# FAQ

**Q** : How do I interpret the alignment string?

**A** : The alignment string is used to indicate matches and mismatches between sequences. For example consider the following alignment

```
ADQSFLWASGVI-S------D-EM--
::::::::::::2:222222:2:122
MHHHHHHSSGVDLWSHPQFEKGT-EN
```
The first 12 residues in the alignment are matches.  The last 2 characters indicate insertions in the second sequence (hence the 2 in the alignment string), and the 3rd to last character indciates an insertion in the first sequence (hence the 1 in the aligment string).

# Citation

If you find our work useful, please cite us at
```
@article{morton2020protein,
  title={Protein Structural Alignments From Sequence},
  author={Morton, Jamie and Strauss, Charlie and Blackwell, Robert and Berenberg, Daniel and Gligorijevic, Vladimir and Bonneau, Richard},
  journal={bioRxiv},
  year={2020},
  publisher={Cold Spring Harbor Laboratory}
}
```
