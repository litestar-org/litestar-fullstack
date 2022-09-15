# Releases

A release should consist of the following two steps from a tested, linted, and up to date copy of the _main_ branch:

1. `make pre-release increment={major/minor/patch}` - Commit the version number bump and create a new tag locally. The version number follows semantic versioning standards (major.minor.patch) and the tag is the version number prepended with a 'v'.

2. `git push --follow-tags` - Update the _main_ branch with only the changes from the version bump. Publish the new tag and kick off the release workflow.
