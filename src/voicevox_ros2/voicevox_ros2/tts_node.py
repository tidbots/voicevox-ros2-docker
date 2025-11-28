# voicevox_ros2/voicevox_ros2.py

import os
import io
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import sounddevice as sd
import soundfile as sf

from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile


class VoicevoxTalker(Node):
    def __init__(self):
        super().__init__("voicevox_talker")

        # --- VOICEVOX Core 初期化 ---
        base_dir = Path(os.environ.get("VOICEVOX_DIR", "."))
        self.get_logger().info(f"VOICEVOX_DIR = {base_dir}")

        onnxruntime_path = base_dir / "onnxruntime" / "lib" / Onnxruntime.LIB_VERSIONED_FILENAME
        open_jtalk_dir = base_dir / "dict" / "open_jtalk_dic_utf_8-1.11"

        self.synthesizer = Synthesizer(
            Onnxruntime.load_once(filename=str(onnxruntime_path)),
            OpenJtalk(str(open_jtalk_dir)),
        )

        # ずんだもんノーマル（style_id = 5）
        self.style_id = 5

        # モデル読み込み
        model_path = base_dir / "models" / "vvms" / "0.vvm"
        with VoiceModelFile.open(str(model_path)) as vm:
            self.synthesizer.load_voice_model(vm)

        self.get_logger().info("VOICEVOX Core 初期化完了")

        # --- Subscriber ---
        self.subscription = self.create_subscription(
            String,
            "/voicevox_tts",
            self.callback_tts,
            10
        )

        self.get_logger().info("Subscribed to /voicevox_tts")

    def callback_tts(self, msg: String):
        text = msg.data.strip()
        if text == "":
            self.get_logger().warn("空文字が送られました")
            return

        self.get_logger().info(f"受信テキスト: {text}")

        # --- 合成（wavバイト列） ---
        wav_bytes = self.synthesizer.tts(text, self.style_id)

        # --- メモリ上で読み込み ---
        data, samplerate = sf.read(io.BytesIO(wav_bytes), dtype="int16")

        # --- 再生 ---
        sd.play(data, samplerate)
        sd.wait()

        self.get_logger().info("再生完了")


def main(args=None):
    rclpy.init(args=args)
    node = VoicevoxTalker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

