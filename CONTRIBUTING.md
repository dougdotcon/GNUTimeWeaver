# Contributing

GNU TimeWeaver accepts focused changes that preserve local execution and make
the native memory model easier to verify.

1. Build with `npm run build`.
2. Run `npm test` before submitting changes.
3. Add a regression test for changes to the disk format, page sharing, lineage,
   checkout, or state reconstruction.
4. Keep network services opt-in. Do not add telemetry or required hosted APIs.
5. Document format changes and bump the on-disk version.

By contributing, you agree that your contribution is licensed under
AGPL-3.0-or-later. Contributions requiring commercial dual licensing are
accepted under a separate Contributor License Agreement.
