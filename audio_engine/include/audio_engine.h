#pragma once
#include <string>
#include <vector>
#include <cstdint>

namespace voicelink {
namespace audio {

struct AudioData {
    int sample_rate = 0;
    int num_channels = 0;
    std::vector<int16_t> samples;
};

struct VoiceSegment {
    int start_sample;
    int end_sample;
};

struct SpeakerSegment {
    int start_sample;
    int end_sample;
    int speaker_id;
};

class AudioEngine {
public:
    AudioEngine() = default;
    void process(const std::string& audio_path);
    AudioData load_wav(const std::string& wav_path);
    AudioData load_mp3(const std::string& mp3_path);
    std::vector<VoiceSegment> detect_voice_segments(const AudioData& data, int frame_ms = 30, int threshold = 500);
    std::vector<VoiceSegment> detect_voice_segments_adaptive(const AudioData& data, int frame_ms = 30, double sensitivity = 2.0);
    std::vector<std::vector<VoiceSegment>> detect_voice_segments_multichannel(const AudioData& data, int frame_ms = 30, int threshold = 500);
    std::vector<SpeakerSegment> diarize(const AudioData& data);
};

int audio_engine_cli(int argc, char** argv);

} // namespace audio
} // namespace voicelink
