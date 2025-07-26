#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "audio_engine.h"

namespace py = pybind11;

PYBIND11_MODULE(audio_engine_py, m) {
    py::class_<voicelink::audio::AudioEngine>(m, "AudioEngine")
        .def(py::init<>())
        .def("process", &voicelink::audio::AudioEngine::process)
        .def("load_wav", &voicelink::audio::AudioEngine::load_wav)
        .def("load_mp3", &voicelink::audio::AudioEngine::load_mp3)
        .def("detect_voice_segments", &voicelink::audio::AudioEngine::detect_voice_segments,
             "Detect voice segments in audio data",
             py::arg("data"), py::arg("frame_ms") = 30, py::arg("threshold") = 500)
        .def("detect_voice_segments_adaptive", &voicelink::audio::AudioEngine::detect_voice_segments_adaptive,
             "Detect voice segments with adaptive threshold",
             py::arg("data"), py::arg("frame_ms") = 30, py::arg("sensitivity") = 2.0)
        .def("detect_voice_segments_multichannel", &voicelink::audio::AudioEngine::detect_voice_segments_multichannel,
             "Detect voice segments for multi-channel audio",
             py::arg("data"), py::arg("frame_ms") = 30, py::arg("threshold") = 500)
        .def("diarize", &voicelink::audio::AudioEngine::diarize);

    py::class_<voicelink::audio::AudioData>(m, "AudioData")
        .def_readwrite("sample_rate", &voicelink::audio::AudioData::sample_rate)
        .def_readwrite("num_channels", &voicelink::audio::AudioData::num_channels)
        .def_readwrite("samples", &voicelink::audio::AudioData::samples);

    py::class_<voicelink::audio::VoiceSegment>(m, "VoiceSegment")
        .def_readwrite("start_sample", &voicelink::audio::VoiceSegment::start_sample)
        .def_readwrite("end_sample", &voicelink::audio::VoiceSegment::end_sample);

    py::class_<voicelink::audio::SpeakerSegment>(m, "SpeakerSegment")
        .def_readwrite("start_sample", &voicelink::audio::SpeakerSegment::start_sample)
        .def_readwrite("end_sample", &voicelink::audio::SpeakerSegment::end_sample)
        .def_readwrite("speaker_id", &voicelink::audio::SpeakerSegment::speaker_id);
}
