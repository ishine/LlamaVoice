import os
from fire import Fire
from typing import Optional
from tqdm import tqdm

import torch
import torchaudio
from safetensors.torch import load_model

from llamavoice.model.llamavoice import LlamaVoiceConfig, LlamaVoice
from llamavoice.utils.mel import extract_linear_features


def main(
    checkpoint_path: str,
    wav_scp: str,
    config: Optional[str] = None,
    save_path: Optional[str] = "analysis_synthesis",
):
    if config and os.path.isfile(config):
        cfg = LlamaVoiceConfig.from_json_file(config)
    else:
        # use default
        cfg = LlamaVoiceConfig()

    model = LlamaVoice(cfg)
    if not checkpoint_path.endswith(".safetensors"):
        model.load_state_dict(torch.load(checkpoint_path))
    else:
        load_model(model, checkpoint_path)
    model.remove_weight_norm()
    model.eval()
    print("model loaded")

    utt2wav = {}
    with open(wav_scp) as f:
        for l in f:
            l = l.strip().split()
            utt2wav[l[0]] = l[1]
    print(f"loaded {len(utt2wav)} utterances")
    os.makedirs(save_path, exist_ok=True)

    for utt, path in tqdm(utt2wav.items()):
        speech, sr = torchaudio.load(path)
        linear = extract_linear_features(speech, cfg=cfg.dataset)
        length = torch.tensor([linear.size(-1)]).to(linear.device)
        output = model.analysis_synthesis(
            {"target_feats": linear, "target_feats_len": length}
        ).predicted_audio
        torchaudio.save(os.path.join(save_path, f"{utt}.wav"), output.squeeze(0), sr)


if __name__ == "__main__":
    Fire(main)
