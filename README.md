# Prompt Override
 An LLM hacking video game.

#### Cite this game
"Prompt Override" will be presented at the 2025 IEEE International Conference on Games (CoG'25) as an *interactive demo*. You can cite this work as follows:
```bibtex
@inproceedings{gallotta2025promptoverride
    title = {Prompt Override: LLM Hacking as Serious Game},
    author = {Roberto Gallotta, Antonios Liapis, Georgios N. Yannakakis},
    year = {2025},
    booktitle = {Proceedings of the International Conference on Games (CoG)}
}
```

#### Trailer
[![Video thumbnail](https://img.youtube.com/vi/RlWYnHZIs0I/0.jpg)](https://www.youtube.com/watch?v=RlWYnHZIs0I)

## Installatation
We recommend creating a new `conda` environment first:
```bash
conda create -n prompt-override python=3.11
```
Then activate it:
```bash
conda activate prompt-override
```
Install required dependencies:
```bash
pip install -r requirementst.txt
```
We make use of Ollama. Follow the instructions at [their website](https://ollama.com/) to install it on your machine. In-game models will be pulled automatically if missing at first launch (it may look like the app has frozen, but it has not).