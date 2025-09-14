# Bathtub Inclines

It's hard to get information about inclines. You can use the TUI app in `bathe.py` to record and view inclines.

Here's the content of the latest DB entries for quick comparison:

```
ID   Name                    Top      Bottom   Width    Height   Incline  Liters     Created     
----------------------------------------------------------------------------------------------------
1    Polypex Siena           176.0    128.0    71.0     44.0     28.61    N/A        2025-09-14
2    Bela (Ideal Standard)   186.6    133.4    78.6     45.0     30.59    315        2025-09-14  
3    Eigenmarke              174.0    146.5    74.0     42.0     18.13    205        2025-09-14  
4    Idea (Ideal Standard)   179.0    136.0    71.0     45.0     25.54    295        2025-09-14  
5    Another (~measurements) 173.0    139.8    74.0     45.0     20.25    N/A        2025-09-14  
```

Entry (1) is the bathtub we tried in the showroom (190 * 85) that felt comfortable but was too expensive.

I think that (2) is likely a good choice, and it seems to be the exact same bathtub that the other plumber suggested.
So that'd also give us the best comparison in terms of cost.

## Setup

Clone the project. Run it with `uv run bathe.py`.

If you don't use uv, first create a venv and install `textual`, then run with `python bathe.py`.

Alternatively, you can view the DB entries also using the CLI `python bathtub_manager.py`.

## Caveats

Some measurements may be inaccurate because of the bathtub edge and because the bottom measurements seem not to be all the way at the bottom (?). You can check out some schemas in `schemas/`. I've tried to account for that in the more recent version of inputs.

Also, this is entirely vibe-coded and I have checked the code only minimally, so the calculations might be wrong 😅
I have however prompted to understand and confirm that the incline is measured from the _vertical_, meaning that higher incline numbers mean less steep (more comfortable to lean against).
