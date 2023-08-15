# Notes

- Won't be as robust as I'd *like*, but should be "good-enough".
- Doesn't currently log group or clan chats, just DMs. This is all I use.
- I don't care about tracking avatars.
- I very very slightly care about emoticons, but we receive the raw
  `[emoticon]emoticonname[/emoticon]` stanzas anyway, and I doubt it'd be that
  hard to source the Steam emoticon images by name, so that could be handled
  entirely by a log-viewer client, doesn't need to be done as part of archival.

## To-Do

- [ ] Track and update known aliases for users, as well as the
  "last"/most-recent/current alias, to ease later viewing of specific DM
  channels
- [ ] Replace print statements with some actual structured logging, or just
  remove
- [ ] Optional auto-archiving of any received link/image/etc. URLs via
  archive.org and/or other archives, to make logs a bit more robust in the face
  of the internet's persistent bitrot
