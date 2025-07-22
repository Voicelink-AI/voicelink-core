#include "audio_engine.h"
#include <cassert>
#include <iostream>
#include <exception>
#include <typeinfo>

int main(int argc, char** argv) {
    std::cout << "test_audio_engine starting..." << std::endl;
    voicelink::audio::AudioEngine engine;
    try {
        std::string file = (argc > 1) ? argv[1] : "sample.wav";
        voicelink::audio::AudioData data;
        if (file.size() > 4 && file.substr(file.size() - 4) == ".mp3") {
            std::cout << "Loading as MP3: " << file << std::endl;
            data = engine.load_mp3(file);
        } else {
            std::cout << "Loading as WAV: " << file << std::endl;
            data = engine.load_wav(file);
        }
        std::cout << "Sample rate: " << data.sample_rate << "\n";
        std::cout << "Channels: " << data.num_channels << "\n";
        std::cout << "Samples: " << data.samples.size() << "\n";
        assert(data.sample_rate > 0);
        assert(data.num_channels > 0);
        assert(!data.samples.empty());

        auto segments = engine.detect_voice_segments(data);
        std::cout << "Detected " << segments.size() << " voice segments (fixed threshold)\n";
        for (const auto& seg : segments) {
            std::cout << "Segment: " << seg.start_sample << " - " << seg.end_sample << "\n";
        }

        auto adaptive_segments = engine.detect_voice_segments_adaptive(data);
        std::cout << "Detected " << adaptive_segments.size() << " voice segments (adaptive threshold)\n";
        for (const auto& seg : adaptive_segments) {
            std::cout << "Segment: " << seg.start_sample << " - " << seg.end_sample << "\n";
        }

        auto multi_segments = engine.detect_voice_segments_multichannel(data);
        std::cout << "Multi-channel VAD: " << multi_segments.size() << " channels\n";
        for (size_t ch = 0; ch < multi_segments.size(); ++ch) {
            std::cout << "Channel " << ch << ": " << multi_segments[ch].size() << " segments\n";
            for (const auto& seg : multi_segments[ch]) {
                std::cout << "  Segment: " << seg.start_sample << " - " << seg.end_sample << "\n";
            }
        }

        auto speaker_segments = engine.diarize(data);
        std::cout << "Diarization segments: " << speaker_segments.size() << "\n";
        for (const auto& seg : speaker_segments) {
            std::cout << "Speaker " << seg.speaker_id << ": " << seg.start_sample << " - " << seg.end_sample << "\n";
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << typeid(e).name() << ": " << e.what() << "\n";
        return 1;
    }
    return 0;
}
