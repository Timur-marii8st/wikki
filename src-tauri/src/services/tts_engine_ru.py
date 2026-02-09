import torch
from pprint import pprint
from omegaconf import OmegaConf
from IPython.display import Audio, display
import os

device = torch.device('cpu')

model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                          model='silero_tts',
                          language='ru',
                          speaker='v5_ru',
                          force_reload=True)

model.to(device)  # gpu or cpu

sample_rate = 48000
speaker = 'baya'
put_accent=True
put_yo=True
put_stress_homo=True
put_yo_homo=True

example_text = 'Меня зовут Лева Королев. Я из готов. И я уже готов открыть все ваши замки любой сложности!'

audio = model.apply_tts(text=example_text,
                        speaker=speaker,
                        sample_rate=sample_rate,
                        put_accent=put_accent,
                        put_yo=put_yo,
                        put_stress_homo=put_stress_homo,
                        put_yo_homo=put_yo_homo)
print(example_text)
display(Audio(audio, rate=sample_rate))

ssml_sample = """
              <speak>
              <p>
                  Когда я просыпаюсь, <prosody rate="x-slow">я говорю довольно медленно</prosody>.
                  Пот+ом я начинаю говорить своим обычным голосом,
                  <prosody pitch="x-high"> а могу говорить тоном выше </prosody>,
                  или <prosody pitch="x-low">наоборот, ниже</prosody>.
                  Пот+ом, если повезет – <prosody rate="fast">я могу говорить и довольно быстро.</prosody>
                  А еще я умею делать паузы любой длины, например, две секунды <break time="2000ms"/>.
                  <p>
                    Также я умею делать паузы между параграфами.
                  </p>
                  <p>
                    <s>И также я умею делать паузы между предложениями</s>
                    <s>Вот например как сейчас</s>
                  </p>
              </p>
              </speak>
              """

sample_rate = 48000
speaker = 'xenia'              
audio = model.apply_tts(ssml_text=ssml_sample,
                        speaker=speaker,
                        sample_rate=sample_rate)
display(Audio(audio, rate=sample_rate))

torchaudio.save('test_audio.wav', audio.unsqueeze(0), sample_rate)