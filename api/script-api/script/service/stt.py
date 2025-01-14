from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from speechbrain.inference.speaker import SpeakerRecognition
import torch
from transformers import (
    AutoModelForSpeechSeq2Seq,
)
import whisperx
import os
import torchaudio
import json

from core.model.domain.script import Script, Record
from script.model.dto.speaker_detect_result import SpeakerDetectResult
from script.model.dto.speaker_modify_result import SpeakerModifyResult
from script.service.llm_service import LLMService
from speechbrain.inference.diarization import Speech_Emotion_Diarization


class SttService:

    def __init__(self, llm_service: LLMService):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # model_id = "freshpearYoon/v3_free_all_re_4000"  # "openai/whisper-large-v3"
        self.batch_size = 16  # reduce if low on GPU mem
        self.compute_type = "float16" if torch.cuda.is_available() else "float32"
        self.model = whisperx.load_model("large-v2", self.device, compute_type=self.compute_type, language="ko")
        self.verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                            savedir="pretrained_models/spkrec-ecapa-voxceleb",
                                                            run_opts={"device": self.device})

        self.sed_model = Speech_Emotion_Diarization.from_hparams(
            source="speechbrain/emotion-diarization-wavlm-large", savedir="./tempdir",
            run_opts={"device": self.device})

        self.llm_service = llm_service

    def run(self, audio_path) -> Script:
        # whisper x 적용
        script = self.make_script(audio_path)

        # speaker check from GPT
        self.adjust_diar(script)

        # first-emotion

        return script

    def adjust_diar(self, script: Script):
        detect_result = self.speaker_detect(script.scripts)
        for record in script.scripts:
            if detect_result.specker_0_is_child:
                if record.speaker == "SPEAKER_0":
                    record.speaker = "C"
                else:
                    record.speaker = "T"
            else:
                if record.speaker == "SPEAKER_0":
                    record.speaker = "T"
                else:
                    record.speaker = "C"

        return script

    def speaker_detect(self, scripts):
        return self.llm_service.run(
            system_prompt="The following is a conversation between child and play-therapist. "
                          "만약 스피커가 아동의 이름을 말하거나 주어가 선생님이~ 로 말한다면 해당 스피커는 선생님이야"
                          "your task is to identify the SPEAKER_0 is child",
            prompt="check next script : {script}",
            variables={"script": scripts[0:20]},
            class_type=SpeakerDetectResult
        )

    # Bad!
    '''
    def gpt_speaker_modify(self, scripts, chunk_size=10):
        for i in range(0, len(scripts), chunk_size):
            chunk = scripts[i:i + chunk_size]
            result = self.llm_service.run(
                system_prompt="The following is a conversation between child and play-therapist. "
                              "your task is to identify the C or T is really child or therapist from context."
                              "if you think the speaker is child, please change the speaker to C. "
                              "if you think the speaker is therapist, please change the speaker to T."
                              "if you don't know, please leave it as it is."
                              "you make list only contain the speaker C or T.",
                prompt="check next script : {script}",
                variables={"script": chunk},
                class_type=SpeakerModifyResult
            )

            try:
                for idx, item in enumerate(chunk):
                    if result.modify_result[idx] == "C":
                        scripts[i + idx]["speaker"] = "C"
                    elif result.modify_result[idx] == "T":
                        scripts[i + idx]["speaker"] = "T"
            except:
                continue

        return scripts
    '''

    def make_script(self, audio_path) -> Script:
        audio = whisperx.load_audio(audio_path)
        result = self.model.transcribe(audio, language="ko", batch_size=self.batch_size)
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        stt_result = whisperx.align(result["segments"],
                                    model_a,
                                    metadata,
                                    audio,
                                    self.device,
                                    return_char_alignments=False)
        # id 적용
        signal, fs = torchaudio.load(audio_path)
        target = stt_result["segments"][0]
        target_signal = self._slice_signal(signal, fs, target['start'], target['end'])
        final_result = Script()
        final_result.scripts.append(
            self._make_script_item(target['text'], target['start'], target['end'], "SPEAKER_0"))
        for seg in stt_result["segments"][1:-1]:
            start_time = seg["start"]
            end_time = seg["end"]

            test_signal = self._slice_signal(signal, fs, start_time, end_time)
            try:
                score, prediction = self.verification.verify_batch(target_signal, test_signal, threshold=0.60)
                if prediction[0][0].cpu():
                    speaker = "SPEAKER_0"
                else:
                    speaker = "SPEAKER_1"
            except:
                speaker = "SPEAKER_0"

            final_result.scripts.append(self._make_script_item(seg["text"], start_time, end_time, speaker))

        # json input typeError 막기 위한 임시방편 코드입니다.
        scripts_as_dicts = [record.dict() for record in final_result.scripts]

        json_file_path = "segments.json"
        with open(json_file_path, 'w', encoding='UTF-8') as json_file:
            # json.dump(final_result.scripts, json_file, ensure_ascii=False, indent=4)
            json.dump(scripts_as_dicts, json_file, ensure_ascii=False, indent=4)
        return final_result

    def _slice_signal(self, waveform, sample_rate, start_time, end_time):
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        return waveform[:, start_sample:end_sample]

    def _compute_time(self, time):
        time = int(time)
        return "{:02d}:{:02d}:{:02d}".format(
            time // 3600, (time % 3600) // 60, time % 60
        )

    def _make_script_item(self, text, start_time, end_time, speaker) -> Record:
        return Record(
            text=text,
            start_time=self._compute_time(start_time),
            end_time=self._compute_time(end_time),
            speaker=speaker,
        )
