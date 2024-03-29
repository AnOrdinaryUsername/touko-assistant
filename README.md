# touko-assistant

A scuffed, personal virtual assistant.

If you are looking for something more performant, check out
[Willow](https://heywillow.io/) or [Jaco](https://gitlab.com/Jaco-Assistant/Jaco-Master)!

## Development

Validate your data

```sh
rasa data validate
```

Train a model

```sh
rasa train
# Alternatively if you have an already trained model and new training datasets
# in nlu/ and domain/ run the following for faster training
rasa train --finetune
```

Start an action server to run [Custom Actions](https://rasa.com/docs/rasa/custom-actions)

```sh
rasa run actions
```

Interact with the latest model on the command line

```sh
rasa shell
# Alternatively, to only see extracted entities and intents from text run
rasa shell nlu
```

## Features

- Tell jokes ✅
- Say the weather ✅
- Time in X place ✅
- Exchange rates
- Bible quotes
- Mangadex chapter feed ✅
- Recipes
- Sports stuff
- News
- Smart home stuff
  - Turn off lights
  - Temperature/Humidity reading
- Print stuff using ESC/POS Thermal Printer
  - Basic text
  - Messages posted by bot
  - Checklist
- Check Calendar
- Set notification
