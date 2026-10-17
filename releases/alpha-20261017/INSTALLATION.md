# Installing PEN-F HSL — 17 October 2026

For the Olympus PEN-F (E122) on official firmware 3.1 or a preceding HSL alpha
based on 3.1. If your camera has older official firmware, update to official
3.1 first. These files are not for another camera model.

## Before installation

Save important settings. With H/L-aware firmware already installed, ordinary
OM Workspace settings backup preserves H/L as well as the stock settings.
The 13 October public alpha does not back up H/L: record important recipes
separately before using a settings restore made on that version.

Upgrading a compatible HSL installation retains its saved H/L values. The
update is not a factory reset. A first installation on stock starts with
neutral H/L. Take note of your existing settings before checking this.

Verify the files against the SHA256 values in README.md. From the extracted
release directory on Linux:

```sh
sha256sum -c SHA256SUMS
```

In Windows PowerShell, check the install file with:

```powershell
Get-FileHash .\install-alpha\DCOLYMP\E1229999.BIN -Algorithm SHA256
```

Compare the entire result with README.md; letter case does not matter.

## SD-card update

1. Select **A** and **Natural** picture mode. Switch off, fully charge the
   battery and disconnect USB. Use a working SD card and back up its photos.
2. Copy **DCOLYMP from install-alpha** to the card root. The exact path must
   be `<card root>/DCOLYMP/E1229999.BIN`. Do not copy the outer release or
   install-alpha directory onto the card. Use only the selected update file.
3. Insert the card with the camera off. Hold **OK** while switching the camera
   on. Release OK once the update indication starts. The screen stays black;
   the AF-assist lamp is steady while updating and blinks rapidly on completion.
   Do not interrupt the steady-light phase or remove the battery. There is no
   established safe forced-stop timeout for an unexpected indication.
4. After the rapid completion blinking, switch off. Remove the update card
   or delete its update file on the computer. Restart normally without holding OK.

The displayed firmware version remains **3.1**. Both main and graphics are
written, even if the Value bitmap was installed previously.

## First checks and editor use

Check Natural shooting, menus and playback. Turn the front creative dial to
COLOR, choose COLOR1/2/3, then open the usual color wheel with the creative
lever. The camera dials select a color and adjust its value.

Tap Delete to cycle **Saturation → Lightness → Hue**. The title, number and
wheel follow the chosen axis. Switching axes alone does not alter the picture.
The selected sector is shared between axes. The axis is remembered when you
reopen the editor, until power-off; a new startup begins on Saturation.

In one profile, try an obvious Lightness change on a visible color, inspect
live view and take RAW+JPEG. Try a small Hue change. Check recorded JPEGs,
profile independence and persistence after a normal restart. Existing users
can compare against their saved settings instead of expecting neutral H/L.

Hold OK on Hue or Lightness to reset that axis to zero. The other axes are
retained. Hold OK on Saturation to restore that profile's stock defaults,
which need not all be zero. Reset H and L separately to neutralize both.

INFO/ALL retains group editing; Delete also cycles axes in ALL. A group step
stops when any color reaches the relevant −7/+7 limit. Extreme combinations
can retain the camera's existing INFO-toggle restrictions.

Custom-mode registration saves the whole camera setup, not only its COLOR
recipe. Editing a recalled mode does not automatically re-register it. Use
the normal camera menu to register or recall C1–C4.

## RAW development and backups

New ORFs carry the captured H/S/L. In Workspace leave Adjust Color unchecked
to use it; enabling that correction overrides it. The added H/L values are
not initialized into Workspace's editable sliders. Other RAW converters are
not established to interpret this native metadata. Older ORFs are unchanged.

In-camera RAW Data Edit Current/Custom uses the selected COLOR profile's
current H/L. RAW Custom1/2 do not get separate H/L banks or an H/L editor;
this is not a new loader for an ORF's as-shot HSL recipe.

The normal Workspace settings save/restore workflow now includes H/L and
restarts the camera after transfer. Old backups without H/L restore neutral
H/L in completed selected banks. Stock JPEG-profile loading is a different
operation: it does not transmit H/L and resets them to neutral.

## Returning to stock or an earlier alpha

**First bring every saved COLOR saturation value within −5…+5, in all three
P/A/S/M profiles and all three profiles of each custom mode.** Save/register
the corrected custom modes as needed. Older firmware's editor cannot
represent −6/−7/+6/+7. An earlier HSL alpha may also neutralize an H/L pair
containing an extended value; save your recipes before downgrading.

To return to stock, repeat the SD update steps using **DCOLYMP from
restore-stock**. This restores the stock main program and original Vivid
bitmap. It does not perform a factory reset or deliberately erase the stored
extension cells. Stock ignores H/L; reinstalling compatible HSL firmware may
restore the saved values. The camera still displays 3.1.

This stock restore is byte-identical to the one used successfully with the
previous public alpha. Recovery from every possible failure is not guaranteed.
