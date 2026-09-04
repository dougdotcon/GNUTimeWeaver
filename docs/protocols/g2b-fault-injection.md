# G2-B2 fault injection

Freeze F01–F23 at staging, header/payload writes, short write, file/directory fsync, reopen, checksum, object/manifest rename, journal update, writer exception, wait timeout and pending shutdown. Every fault must leave no falsely complete manifest and must be observable in the journal.
