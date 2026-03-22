# Mesh Devices

- Study
https://github.com/rustonbsd/libp2p-iroh/tree/main

- Study 
https://github.com/n0-computer/iroh

- Read 

# Jeff Gerrling
Gemini said
Here is the transcription of the text in the image:

Jeff Geerling @geerlingguy · 18h

LM Studio emailed me yesterday and invited me to test this — I've been using Wireguard and llama.cpp to run large models on my studio workstations, from anywhere.

(I run a few local LLMs to help with MicroPython, debugging PTP, that sort of thing...)

I'm attaching a video showing LM Studio running on my low-spec Mac mini at home, using a large model running on a Dell GB10 at the studio. Also tested it running through my Mac Studio at the studio.

They use Tailscale on the backend, but it's separate from Tailscale (managed through LM Studio)—works well, but I still prefer llama.cpp since it's open source. The llama.cpp Web GUI makes it easy enough (for me) to use on the road via VPN, through a browser.

I haven't really messed with LM Studio or vLLM before, but I can see the appeal, especially if you link LLMs to external tools (I don't, at least not at this time).

The screenshot at the bottom shows a terminal-style chat interface with the following commands:

sudo apt update && sudo apt install inotify-tools ffmpeg

Verify ffmpeg has HEVC support (standard on Debian):

# Goal
Replicating this using libp2p as the connection solution



