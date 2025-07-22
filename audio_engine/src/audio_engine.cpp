#define MINIMP3_IMPLEMENTATION
#define MINIMP3_EX_IMPLEMENTATION
#include "minimp3.h"
#include "minimp3_ex.h"

#include "audio_engine.h"
#include <fstream>
#include <stdexcept>
#include <cstring>
#include <cmath>
#include <iostream>

namespace voicelink {
namespace audio {

void AudioEngine::process(const std::string& audio_path) {
    AudioData data = load_wav(audio_path);
    auto segments = detect_voice_segments(data);
}

AudioData AudioEngine::load_wav(const std::string& wav_path) {
    std::ifstream file(wav_path, std::ios::binary);
    if (!file) throw std::runtime_error("Cannot open WAV file");

    char riff[4];
    file.read(riff, 4);
    if (std::strncmp(riff, "RIFF", 4) != 0) throw std::runtime_error("Not a RIFF file");

    file.ignore(4); // file size

    char wave[4];
    file.read(wave, 4);
    if (std::strncmp(wave, "WAVE", 4) != 0) throw std::runtime_error("Not a WAVE file");

    char fmt[4];
    file.read(fmt, 4);
    if (std::strncmp(fmt, "fmt ", 4) != 0) throw std::runtime_error("Missing fmt chunk");

    uint32_t fmt_size = 0;
    file.read(reinterpret_cast<char*>(&fmt_size), 4);
    file.ignore(2); // audio format
    uint16_t num_channels = 0;
    file.read(reinterpret_cast<char*>(&num_channels), 2);
    uint32_t sample_rate = 0;
    file.read(reinterpret_cast<char*>(&sample_rate), 4);
    file.ignore(6); // byte rate + block align
    uint16_t bits_per_sample = 0;
    file.read(reinterpret_cast<char*>(&bits_per_sample), 2);
    file.ignore(fmt_size - 16); // skip the rest of fmt chunk if any

    // find "data" chunk
    char chunk_id[4];
    uint32_t chunk_size = 0;
    while (file.read(chunk_id, 4)) {
        file.read(reinterpret_cast<char*>(&chunk_size), 4);
        if (std::strncmp(chunk_id, "data", 4) == 0) break;
        file.ignore(chunk_size);
    }
    if (std::strncmp(chunk_id, "data", 4) != 0) throw std::runtime_error("Missing data chunk");

    std::vector<int16_t> samples(chunk_size / 2);
    file.read(reinterpret_cast<char*>(samples.data()), chunk_size);

    AudioData data;
    data.sample_rate = sample_rate;
    data.num_channels = num_channels;
    data.samples = std::move(samples);
    return data;
}

AudioData AudioEngine::load_mp3(const std::string& mp3_path) {
    std::cout << "[load_mp3] Opening file: " << mp3_path << std::endl;
    mp3dec_ex_t dec;
    int open_result = mp3dec_ex_open(&dec, mp3_path.c_str(), MP3D_SEEK_TO_SAMPLE);
    std::cout << "[load_mp3] mp3dec_ex_open result: " << open_result << std::endl;
    if (open_result) {
        std::cerr << "[load_mp3] Cannot open MP3 file: " << mp3_path << std::endl;
        throw std::runtime_error("Cannot open MP3 file");
    }
    std::cout << "[load_mp3] MP3 info: sample_rate=" << dec.info.hz
              << ", channels=" << dec.info.channels
              << ", samples=" << dec.samples << std::endl;
    AudioData data;
    data.sample_rate = dec.info.hz;
    data.num_channels = dec.info.channels;
    size_t nsamples = dec.samples;
    data.samples.resize(nsamples);
    if (nsamples > 0 && dec.buffer) {
        std::memcpy(data.samples.data(), dec.buffer, nsamples * sizeof(int16_t));
    } else {
        std::cerr << "[load_mp3] No samples decoded or buffer is null." << std::endl;
    }
    mp3dec_ex_close(&dec);
    std::cout << "[load_mp3] Done loading MP3." << std::endl;
    return data;
}

std::vector<VoiceSegment> AudioEngine::detect_voice_segments(const AudioData& data, int frame_ms, int threshold) {
    std::vector<VoiceSegment> segments;
    if (data.sample_rate == 0 || data.samples.empty()) return segments;

    int frame_size = (data.sample_rate * frame_ms) / 1000;
    bool in_voice = false;
    int seg_start = 0;

    for (size_t i = 0; i + frame_size <= data.samples.size(); i += frame_size) {
        double energy = 0.0;
        for (int j = 0; j < frame_size; ++j) {
            energy += std::abs(data.samples[i + j]);
        }
        energy /= frame_size;

        if (energy > threshold) {
            if (!in_voice) {
                seg_start = static_cast<int>(i);
                in_voice = true;
            }
        } else {
            if (in_voice) {
                segments.push_back({seg_start, static_cast<int>(i)});
                in_voice = false;
            }
        }
    }
    if (in_voice) {
        segments.push_back({seg_start, static_cast<int>(data.samples.size())});
    }
    return segments;
}

std::vector<VoiceSegment> AudioEngine::detect_voice_segments_adaptive(const AudioData& data, int frame_ms, double sensitivity) {
    std::vector<VoiceSegment> segments;
    if (data.sample_rate == 0 || data.samples.empty()) return segments;

    int frame_size = (data.sample_rate * frame_ms) / 1000;
    std::vector<double> energies;
    for (size_t i = 0; i + frame_size <= data.samples.size(); i += frame_size) {
        double energy = 0.0;
        for (int j = 0; j < frame_size; ++j) {
            energy += std::abs(data.samples[i + j]);
        }
        energy /= frame_size;
        energies.push_back(energy);
    }

    double mean = 0.0, sq_sum = 0.0;
    for (double e : energies) mean += e;
    mean /= energies.size();
    for (double e : energies) sq_sum += (e - mean) * (e - mean);
    double stddev = std::sqrt(sq_sum / energies.size());
    double threshold = mean + sensitivity * stddev;

    bool in_voice = false;
    int seg_start = 0;
    for (size_t i = 0; i < energies.size(); ++i) {
        if (energies[i] > threshold) {
            if (!in_voice) {
                seg_start = static_cast<int>(i * frame_size);
                in_voice = true;
            }
        } else {
            if (in_voice) {
                segments.push_back({seg_start, static_cast<int>(i * frame_size)});
                in_voice = false;
            }
        }
    }
    if (in_voice) {
        segments.push_back({seg_start, static_cast<int>(data.samples.size())});
    }
    return segments;
}

std::vector<std::vector<VoiceSegment>> AudioEngine::detect_voice_segments_multichannel(const AudioData& data, int frame_ms, int threshold) {
    std::vector<std::vector<VoiceSegment>> all_segments;
    if (data.sample_rate == 0 || data.samples.empty() || data.num_channels <= 1) {
        // fallback: treat as mono
        all_segments.push_back(detect_voice_segments(data, frame_ms, threshold));
        return all_segments;
    }

    int frame_size = (data.sample_rate * frame_ms) / 1000;
    int num_frames = static_cast<int>(data.samples.size()) / data.num_channels / frame_size;

    for (int ch = 0; ch < data.num_channels; ++ch) {
        std::vector<VoiceSegment> segments;
        bool in_voice = false;
        int seg_start = 0;
        for (int f = 0; f < num_frames; ++f) {
            double energy = 0.0;
            int base = (f * frame_size * data.num_channels) + ch;
            for (int j = 0; j < frame_size; ++j) {
                int idx = base + j * data.num_channels;
                if (idx < data.samples.size())
                    energy += std::abs(data.samples[idx]);
            }
            energy /= frame_size;

            int frame_start = (f * frame_size);
            if (energy > threshold) {
                if (!in_voice) {
                    seg_start = frame_start;
                    in_voice = true;
                }
            } else {
                if (in_voice) {
                    segments.push_back({seg_start, frame_start});
                    in_voice = false;
                }
            }
        }
        if (in_voice) {
            segments.push_back({seg_start, num_frames * frame_size});
        }
        all_segments.push_back(segments);
    }
    return all_segments;
}

std::vector<SpeakerSegment> AudioEngine::diarize(const AudioData& data) {
    std::vector<SpeakerSegment> segments;
    if (data.num_channels > 1) {
        // treat each channel as a different speaker
        int samples_per_channel = static_cast<int>(data.samples.size() / data.num_channels);
        for (int ch = 0; ch < data.num_channels; ++ch) {
            segments.push_back({ch * samples_per_channel, (ch + 1) * samples_per_channel, ch});
        }
    } else if (!data.samples.empty()) {
        // fallback: single speaker for mono
        segments.push_back({0, static_cast<int>(data.samples.size()), 0});
    }
    return segments;
}

int audio_engine_cli(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <wavfile> [--vad] [--diarize]\n";
        return 1;
    }
    std::string wavfile = argv[1];
    bool do_vad = false, do_diar = false;
    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--vad") do_vad = true;
        if (arg == "--diarize") do_diar = true;
    }

    AudioEngine engine;
    try {
        auto data = engine.load_wav(wavfile);
        std::cout << "Sample rate: " << data.sample_rate << "\n";
        std::cout << "Channels: " << data.num_channels << "\n";
        std::cout << "Samples: " << data.samples.size() << "\n";

        if (do_vad) {
            auto segments = engine.detect_voice_segments(data);
            std::cout << "Detected " << segments.size() << " voice segments\n";
            for (const auto& seg : segments) {
                std::cout << "Segment: " << seg.start_sample << " - " << seg.end_sample << "\n";
            }
        }
        if (do_diar) {
            auto speaker_segments = engine.diarize(data);
            std::cout << "Diarization segments: " << speaker_segments.size() << "\n";
            for (const auto& seg : speaker_segments) {
                std::cout << "Speaker " << seg.speaker_id << ": " << seg.start_sample << " - " << seg.end_sample << "\n";
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}

} // namespace audio
} // namespace voicelink
