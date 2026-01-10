# FFmpeg to PATH Installer

## Explanation

A lot of programs, python scripts and such that deal with audio files or video files often need 'FFmpeg' to edit the files and do cool automations with them. 

FFmpeg itself is a collection of code packed into a compiled program that does the hard work behind the scenes for many of such programs that work with audio/video files. On the Windows Personal Computer Operating System, FFmpeg can be installed to what is called an 'Windows PATH environment variable', which will give access to programs to use FFmpeg easily so that they will actually work.

A lot of my own programs use FFmpeg if they deal with audio or video files. The problem is that trying to bundle FFmpeg with my programs causes them to balloon to 100MB or more in filesize, taking up space and making the program slower and more bothersome to compile into an exe. So instead, I made this:

A simple GUI application that automatically installs FFmpeg to Windows PATH for easy access by other applications.

## Features

- Downloads official FFmpeg builds automatically.
- Installs to C:\ffmpeg.
- Adds FFmpeg to Windows PATH environment variable.
- Simple GUI interface for laypeople - everything handled with a single click.
- One-click installation verification, allowing to check if you already have it.
- Easy uninstall functionality included too.
- Supports Windows 7-through-11-and-above.

## Usage

1. Run `FFmpeg_PATH_Installer.exe`
2. Click "Install FFmpeg to PATH" 
3. Wait for download and installation to complete
4. Restart applications that need FFmpeg
5. Use "Check Installation" to verify it's working

## What it does

- It downloads FFmpeg from https://www.gyan.dev/ffmpeg/builds/
- It extracts to C:\ffmpeg
- It adds C:\ffmpeg\bin to Windows PATH
- It makes FFmpeg available system-wide

This allows my 'ElevenLabs Batch Transcriber' and many other applications to use FFmpeg without bundling it. Saves a lot of hard drive space and makes for smaller downloads, yay.
(Find my other cool programs here: https://reactorcore.itch.io/)


## Support My Work

If my work is helping you, here's how you can support me too:

Buy me an orange as a one-off gift:
https://buymeacoffee.com/reactorcoregames

Join as a Patreon member for tons of benefits: 
https://www.patreon.com/ReactorcoreGames

Donate, buy, try my other itch.io releases: 
https://reactorcore.itch.io/

Share my linktree or discord with people:
http://www.reactorcoregames.com
https://discord.gg/UdRavGhj47

Hire me or recommend me for full-time work as a Game Designer or Prompt Engineer:
mailto:reactorcoregames@gmail.com
(I can do Advanced Game Design Plans/Consulting, Build Standalone Offline Web Apps or Automation Software With Python)

My Game Design Portfolio:
https://reactorcoregames.github.io/game-design-showcase-portfolio/

Enjoy! B-)
- Reactorcore