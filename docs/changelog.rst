=========
Changelog
=========

All commits to this project will be documented in this file.

[unreleased]
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Bug Fixes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`e134a29 <https://github.com/litestar-org/litestar-fullstack/commit/e134a29bed11ec6b69af5614e5db99ab70b66e40>`_)  - Set volume mounts explicitly to avoid mounting `.venv` and `node_modules` not built in the container. (Cody Fincher)
* (`cb80d8e <https://github.com/litestar-org/litestar-fullstack/commit/cb80d8eae6f7c12aff537d911ee79a31123a6e00>`_)  - Correct test case (Cody Fincher)
* (`0900927 <https://github.com/litestar-org/litestar-fullstack/commit/0900927c4cda4858ea7b4b4d9ae41e28b7b81a7b>`_)  - Updated pre-commit config (Cody Fincher)
* (`875c672 <https://github.com/litestar-org/litestar-fullstack/commit/875c672ccb451b341db3c66ada10957916bfcb05>`_)  - Tests update (Cody Fincher)
* (`7ec1e02 <https://github.com/litestar-org/litestar-fullstack/commit/7ec1e02e079438213adf3180c0b159e687f7a55d>`_)  - Cleanup the output. remove useless except block (Cody Fincher)
* (`c635168 <https://github.com/litestar-org/litestar-fullstack/commit/c635168ca39df63da14c27ef008f6ecc1f84c02f>`_)  - Logging cleanup (Cody Fincher)
* (`2c35d8e <https://github.com/litestar-org/litestar-fullstack/commit/2c35d8efbfdf67b167e349a1fa42ddc19d8804c4>`_)  - Corrected type hints (Cody Fincher)
* (`d3b8f62 <https://github.com/litestar-org/litestar-fullstack/commit/d3b8f62126bde427940a035af86fb23d593e6386>`_)  - Updated test cases (Cody Fincher)
* (`b407044 <https://github.com/litestar-org/litestar-fullstack/commit/b407044909caf2286474e7880cf86fc5a30c85da>`_)  - Ensure logger is configured in worker processes (Cody Fincher)
* (`c8e1bab <https://github.com/litestar-org/litestar-fullstack/commit/c8e1bab25f01573bde7c75e263d29efaee3f18df>`_)  - Update name (Cody Fincher)
* (`968d8a8 <https://github.com/litestar-org/litestar-fullstack/commit/968d8a8abf905a3535c909c3dae13cd8dbee4476>`_)  - Updated symlink path for build dir.  Moved web folder. (Cody Fincher)
* (`02c1b7b <https://github.com/litestar-org/litestar-fullstack/commit/02c1b7bef49f13d6ef5d688aaed411a3e6fd7e34>`_)  - Simplify expression (Cody Fincher)
* (`1b7a54e <https://github.com/litestar-org/litestar-fullstack/commit/1b7a54e2c9d0e2371063ee05dc77fb633ed0ebef>`_)  - Updated startup configuration.  add exists statement. (Cody Fincher)
* (`52e09ec <https://github.com/litestar-org/litestar-fullstack/commit/52e09ecb891e630aa8a6f6388cd4536fe2cd11c7>`_)  - Version updates (Cody Fincher)
* (`f2e07da <https://github.com/litestar-org/litestar-fullstack/commit/f2e07da3a90b943d7e6c203addfadaf04d874eb8>`_)  - Squashed and re-applied migrations as a test.  Please reset database if you've used the DB already. (Cody Fincher)
* (`275ef1b <https://github.com/litestar-org/litestar-fullstack/commit/275ef1bb6b5d16b803a975b881541c210608cf54>`_)  - Adds tailwind and existing js dotfiles to node container (Cody Fincher)
* (`304b249 <https://github.com/litestar-org/litestar-fullstack/commit/304b249f074bd3bee2eb874f1cad1d62e250f681>`_)  - Pass kwargs into structlog.getLogger (Cody Fincher)
* (`5addca6 <https://github.com/litestar-org/litestar-fullstack/commit/5addca6e9d72a4ef61f9386dffdf3095ef626621>`_)  - Slight re-org (Cody Fincher)
* (`4c642ea <https://github.com/litestar-org/litestar-fullstack/commit/4c642eaab5e17d0afa1e40173008b30bb729b0b4>`_)  - Remove the need for an extra file. (Cody Fincher)
* (`292ea06 <https://github.com/litestar-org/litestar-fullstack/commit/292ea0638edf1452a7d4264abcef790dcffe7851>`_)  - Remove unnecessary try/finally (Cody Fincher)
* (`72dc79c <https://github.com/litestar-org/litestar-fullstack/commit/72dc79c92ee36f93192cf9b30b9e9cf150003f6b>`_)  - Rename logger -> log (Cody Fincher)
* (`6432fa8 <https://github.com/litestar-org/litestar-fullstack/commit/6432fa8b50261af8c816de917a342d75a0f0448f>`_)  - Correct endpoint path (Cody Fincher)
* (`1e37673 <https://github.com/litestar-org/litestar-fullstack/commit/1e37673f26604d64348c26d07a23c8bee80c36c0>`_)  - Remove unused logger calls (Cody Fincher)
* (`b74bb0f <https://github.com/litestar-org/litestar-fullstack/commit/b74bb0ffe036a5b4595b7228913afd3d8e3c8607>`_)  - Split user controllers into separate files (Cody Fincher)
* (`d135cf2 <https://github.com/litestar-org/litestar-fullstack/commit/d135cf2ce768fe3b4232d71329ff6faddfdcde04>`_)  - Simplify repo (Cody Fincher)
* (`df3c0cd <https://github.com/litestar-org/litestar-fullstack/commit/df3c0cd002241a6c97da4fa69ecedd3ce6079539>`_)  - Remove symlink (Cody Fincher)
* (`17f6d3d <https://github.com/litestar-org/litestar-fullstack/commit/17f6d3d4ab0906b713db6bbbe98db0993e0c2ad2>`_)  - Remove extra ignore (Cody Fincher)
* (`ab502b6 <https://github.com/litestar-org/litestar-fullstack/commit/ab502b68e922a3e547ac336ea5380745b7e9498d>`_)  - Simplify worker command (Cody Fincher)
* (`10c6ca5 <https://github.com/litestar-org/litestar-fullstack/commit/10c6ca53be75308553634eb35872b0b34bb37551>`_)  - Swap to distroless (Cody Fincher)
* (`f135b5d <https://github.com/litestar-org/litestar-fullstack/commit/f135b5df650f122e849f02aeef6489bec4431351>`_)  - Finish swap to distroless 3.11 (Cody Fincher)
* (`f2a5d2e <https://github.com/litestar-org/litestar-fullstack/commit/f2a5d2e8e713ca8710f77a79e794bb904c4eb846>`_)  - Additional docker cleanup (Cody Fincher)
* (`fb5290c <https://github.com/litestar-org/litestar-fullstack/commit/fb5290c92476c98c392b4802dc32e4f9d6646c32>`_)  - Adjusts config (Cody Fincher)
* (`b4c86b6 <https://github.com/litestar-org/litestar-fullstack/commit/b4c86b6b6023bedab43980922068d7fa8b452930>`_)  - Remove example endpoint.  adjust vite config (Cody Fincher)
* (`cbf96d6 <https://github.com/litestar-org/litestar-fullstack/commit/cbf96d6b3c67b4147bf535a779270596b4141af8>`_)  - Adds in the asset directory of vite as a static path when running in dev mode (Cody Fincher)
* (`0a5747b <https://github.com/litestar-org/litestar-fullstack/commit/0a5747b6ff6823acebbd39215c2c48a5a592e9c8>`_)  - Ignore changes to public dir.  this is populated by `npm run build` (Cody Fincher)
* (`1adab79 <https://github.com/litestar-org/litestar-fullstack/commit/1adab796f0599bd2a368f433fec02d0b117c6a3a>`_)  - Correct reference (Cody Fincher)
* (`2de8619 <https://github.com/litestar-org/litestar-fullstack/commit/2de861976f4f25e41a0be277f0873259340b9dda>`_)  - Variable name usage (Cody Fincher)
* (`dabfc84 <https://github.com/litestar-org/litestar-fullstack/commit/dabfc84715ede4af8c51d4b6fe53451bbd194b41>`_)  - Rename methods to private (Cody Fincher)
* (`2b33371 <https://github.com/litestar-org/litestar-fullstack/commit/2b333710941eab742db41901b79c2bc52efbf5fc>`_)  - Assume public is unchanged.  This prevents the changes from a build showing here. (Cody Fincher)
* (`0a966e0 <https://github.com/litestar-org/litestar-fullstack/commit/0a966e09bd3dda626dbb4e92cce26fb0da16b5ad>`_)  - Adds polyfill required for running with a remote backend (Cody Fincher)
* (`64634cb <https://github.com/litestar-org/litestar-fullstack/commit/64634cb10972b8df522ca54ed1ca30667b4e0ba0>`_)  - Adds additional ruff checks (Cody Fincher)
* (`b25edd1 <https://github.com/litestar-org/litestar-fullstack/commit/b25edd1a07d31627ba50778d06cb2ddb89e63f4b>`_)  - Linting updates (Cody Fincher)
* (`02c99ee <https://github.com/litestar-org/litestar-fullstack/commit/02c99ee09f05147800b279737e87dcef54013ea4>`_)  - Doc updates (Cody Fincher)
* (`958aa30 <https://github.com/litestar-org/litestar-fullstack/commit/958aa307c196bbf0bcf734a1e66c059e7b6eef65>`_)  - Remove unused reference to GCP service account (Cody Fincher)
* (`27fcac2 <https://github.com/litestar-org/litestar-fullstack/commit/27fcac2e51621a18d3ae3b3f721f1fefc4d06830>`_)  - Move into type checking block (Cody Fincher)
* (`dc86c8b <https://github.com/litestar-org/litestar-fullstack/commit/dc86c8b5aec8b757ada02e9703c124a66f39ab73>`_)  - Swap to AsyncCallable (Cody Fincher)
* (`b7f7621 <https://github.com/litestar-org/litestar-fullstack/commit/b7f7621a49118c342dd5c5f8e6304057e519b613>`_)  - Enable UI build and integration into docker image (Cody Fincher)
* (`a35fc31 <https://github.com/litestar-org/litestar-fullstack/commit/a35fc31db2f9ce911fd22e55bb194a18b767ddd8>`_)  - Updated container (Cody Fincher)
* (`dd64785 <https://github.com/litestar-org/litestar-fullstack/commit/dd64785c000f90dbb9947f17a916949c396fc361>`_)  - Permissions in build image for running it as non-root in dev (Cody Fincher)
* (`73cdb05 <https://github.com/litestar-org/litestar-fullstack/commit/73cdb05636da840be81964dc3f0edadc16176cc6>`_)  - Cleanup (Cody Fincher)
* (`461e171 <https://github.com/litestar-org/litestar-fullstack/commit/461e1714e4411e30d598f0b049ffc2810354b697>`_)  - Updates configuration to use recently merged response_cache & stores config (Cody Fincher)
* (`b0089bf <https://github.com/litestar-org/litestar-fullstack/commit/b0089bfe92dcc451d901f2552698f7b13a429f54>`_)  - Call uvicorn as a subprocess. (Cody Fincher)
* (`c2d935c <https://github.com/litestar-org/litestar-fullstack/commit/c2d935cd5c4bb39290bddb69f6cc3d24da334a5b>`_)  - Update forward refs.  fixes 1 of 2 issues for inserts (Cody Fincher)
* (`b405aa3 <https://github.com/litestar-org/litestar-fullstack/commit/b405aa350097e017032ea11552dd4e1e9fe7ec9b>`_)  - Correctly call model from dict for all methods (Cody Fincher)
* (`1a32a2c <https://github.com/litestar-org/litestar-fullstack/commit/1a32a2c25eeb58fdfa8791b24da447cd37857cdb>`_)  - UUID serializer issue (Cody Fincher)
* (`3310e37 <https://github.com/litestar-org/litestar-fullstack/commit/3310e3753428164c396b9daa631bb0818ce0f63b>`_)  - Updated provide user (Cody Fincher)
* (`1498dfe <https://github.com/litestar-org/litestar-fullstack/commit/1498dfefa8c3875753640ebad2636ade601e9763>`_)  - Additional 2.0 adjustments (Cody Fincher)
* (`ea7f1f5 <https://github.com/litestar-org/litestar-fullstack/commit/ea7f1f5a311b1b420eb08d1a73354a250ebf2347>`_)  - Move `joined_at` and `verified_at` to datetime (Cody Fincher)
* (`2fa75a3 <https://github.com/litestar-org/litestar-fullstack/commit/2fa75a353e64e58b41e131e4fe14bd1bf3ffd99d>`_)  - Return User schema instead of user model (Cody Fincher)
* (`ebbcce5 <https://github.com/litestar-org/litestar-fullstack/commit/ebbcce55ea28183dfdd4aa23f7c4281f357839f9>`_)  - `Request` has no attribute `to_dict` error (Cody Fincher)
* (`ec798ad <https://github.com/litestar-org/litestar-fullstack/commit/ec798adb77eb56dabc45da80f32f111e383917e2>`_)  - Adds worker command and updated CLI markdown (Cody Fincher)
* (`257260d <https://github.com/litestar-org/litestar-fullstack/commit/257260d25fcc9b1b086ce7191d7eb6b6d5ecdcdf>`_)  - Remove extra tag from User controller (Cody Fincher)
* (`d7f0e41 <https://github.com/litestar-org/litestar-fullstack/commit/d7f0e41733886dfd690547fd270bc00cb89b7164>`_)  - Prevent duplicate log messages from the `sqlalchemy.pool` loggers. (Cody Fincher)
* (`315a6c8 <https://github.com/litestar-org/litestar-fullstack/commit/315a6c8ed7f63fa80a87bb1d2315df8cbcf008d9>`_)  - Updated build process & repository enhancements (#13) (Cody Fincher)
* (`0be2059 <https://github.com/litestar-org/litestar-fullstack/commit/0be2059a41e6684c3540353107a4c042a03be5f4>`_)  - Updated process handling & run as factory (Cody Fincher)
* (`e8614ec <https://github.com/litestar-org/litestar-fullstack/commit/e8614ec7779f608c78a56aec871a6521d92f09e4>`_)  - Re-add accidentally removed `profile` route (Cody Fincher)
* (`8de65f0 <https://github.com/litestar-org/litestar-fullstack/commit/8de65f09a2e144800abd37db2a18a25723ed9bd4>`_)  - Additional tests and adjusted dependency (Cody Fincher)
* (`15b9901 <https://github.com/litestar-org/litestar-fullstack/commit/15b9901a0ebcb1158a3c38268bfa039a811fe39f>`_)  - Move aiosql into query files.  Add paginated results helper (Cody Fincher)
* (`14f841c <https://github.com/litestar-org/litestar-fullstack/commit/14f841c4d7baaf558422a26225dd4bebc9db2cc3>`_)  - Enable base model caching (Cody Fincher)
* (`2ef4c2e <https://github.com/litestar-org/litestar-fullstack/commit/2ef4c2e4841906cd10ce18a590bfaea97505ed4f>`_)  - Simplify aiosql class (Cody Fincher)
* (`40f392f <https://github.com/litestar-org/litestar-fullstack/commit/40f392f4495b13a6a4238e3c3bd2c13324b2feab>`_)  - Remove extra variable (Cody Fincher)
* (`ad0b612 <https://github.com/litestar-org/litestar-fullstack/commit/ad0b61265610ac18b73701fdf4701f137d99d04d>`_)  - Remove the `from_orm` override in preference of a `association_proxy` (Cody Fincher)
* (`e2787b0 <https://github.com/litestar-org/litestar-fullstack/commit/e2787b0788469a99faa321818591a088515a2d6d>`_)  - Corrected test cases. (Cody Fincher)
* (`0627aa5 <https://github.com/litestar-org/litestar-fullstack/commit/0627aa525d2af5b5472965f87ec5ba29b4289a0c>`_)  - Remove extra ``DB_`` prefix from a few settings (#18) (Patrick Armengol)
* (`0f4140d <https://github.com/litestar-org/litestar-fullstack/commit/0f4140d71988768db402ca3e8fa8cfc9c700e99c>`_)  - Various test case corrections and enhancements (Cody Fincher)
* (`0589818 <https://github.com/litestar-org/litestar-fullstack/commit/0589818ef01012b671c2ee609ecc8b2d187222cf>`_)  - Corrects tests and worker launch process (#21) (Cody Fincher)
* (`b1a62a9 <https://github.com/litestar-org/litestar-fullstack/commit/b1a62a98192cbfcffc0526b25e226a23db27934c>`_)  - Corrections to docker build process (#33) (Cody Fincher)
* (`31bda77 <https://github.com/litestar-org/litestar-fullstack/commit/31bda77fe5a7093e62f2003c5511b2cff8f5b7c2>`_)  - Correct run command (Cody Fincher)
* (`19de705 <https://github.com/litestar-org/litestar-fullstack/commit/19de7054191bf9eb731662baec7a3b6f592b213b>`_)  - Remove unused make entry.  updated env example (Cody Fincher)
* (`110c1e8 <https://github.com/litestar-org/litestar-fullstack/commit/110c1e81fe7da6d15f1a16c2cbf7d0a6d2a77cf6>`_)  - Adds local flag to poetry config. (Cody Fincher)
* (`4d70b37 <https://github.com/litestar-org/litestar-fullstack/commit/4d70b3713552df77b0146fd5ef1a1337fc6aac90>`_)  - Migrate to updated model names for sqlalchemy (Cody Fincher)
* (`918d45d <https://github.com/litestar-org/litestar-fullstack/commit/918d45d74674db6d4725808c15c0b38a2eb10743>`_)  - Correct remaining test case for filter deps (Cody Fincher)
* (`07e5c79 <https://github.com/litestar-org/litestar-fullstack/commit/07e5c79aa2d30416f85902f3faf06a7baade932f>`_)  - Address new `sync_to_thread` warnings and other test fixes (Cody Fincher)
* (`7b3f20b <https://github.com/litestar-org/litestar-fullstack/commit/7b3f20bcc75eb826cf7da7adc5fde6676a99dadd>`_)  - Use self-hosted saq UI (Cody Fincher)
* (`f16c82e <https://github.com/litestar-org/litestar-fullstack/commit/f16c82edee119f4239a09bea6817c1c25067909e>`_)  - Update timeout to prevent max job duration from exceeding. (Cody Fincher)
* (`1abf102 <https://github.com/litestar-org/litestar-fullstack/commit/1abf1028df18733b8ae5669e32c5f543cb8e5cb5>`_)  - Remove extra call (Cody Fincher)
* (`4c35cbb <https://github.com/litestar-org/litestar-fullstack/commit/4c35cbb0f1dd819667e295a2908fd2f362d59ff9>`_)  - Version bumps (Cody Fincher)
* (`81d3343 <https://github.com/litestar-org/litestar-fullstack/commit/81d33439a87d44ab1dcd93b8d824f83ef37f0658>`_)  - Moved signature namespace from `asgi.py`, separated `aiosql` module for easier removal. (Cody Fincher)
* (`1790f80 <https://github.com/litestar-org/litestar-fullstack/commit/1790f80487291d003e9a516e2f5f14a90817a1f4>`_)  - Parameter has been removed upstream (Cody Fincher)
* (`2d00d73 <https://github.com/litestar-org/litestar-fullstack/commit/2d00d73ba8248a436eeeaa22a3cee90cbca3f2fe>`_)  - Additional updates for upstream changes. (Cody Fincher)
* (`d46df10 <https://github.com/litestar-org/litestar-fullstack/commit/d46df10104eade752abac6585acf3e8f4e3efef3>`_)  - Adds updates tests (Cody Fincher)
* (`85bfbc8 <https://github.com/litestar-org/litestar-fullstack/commit/85bfbc86118ff18ca027b64ce9f63d940854fc32>`_)  - Upgrade to litestar beta.  squashed migrations to enabled DateTimeUTC columns. (Cody Fincher)
* (`90031f8 <https://github.com/litestar-org/litestar-fullstack/commit/90031f82a087de3c79eac902492cc02a13f3b668>`_)  - Updated readme (Cody Fincher)
* (`bc6ef7f <https://github.com/litestar-org/litestar-fullstack/commit/bc6ef7ff3fee74fa6df16bda68b56b0360b50bd4>`_)  - Updated readme (Cody Fincher)
* (`14c588a <https://github.com/litestar-org/litestar-fullstack/commit/14c588ae53238d8f2e52e50ae037536d1b2542d9>`_)  - Remove outdated type_encoder (Cody Fincher)
* (`f474ce4 <https://github.com/litestar-org/litestar-fullstack/commit/f474ce4813029740a15783e16d45acda7f81023f>`_)  - Updates for the orm sentinel changes (Cody Fincher)
* (`3ef9264 <https://github.com/litestar-org/litestar-fullstack/commit/3ef9264eba4a1d1735e8fbf2707d950b3a765511>`_)  - Pydantic v2 support + latest litestar support (Cody Fincher)
* (`4c83899 <https://github.com/litestar-org/litestar-fullstack/commit/4c838990e09d0f17d6bb0aab5ff0883a6f7e2c55>`_)  - Docker build improvements (Cody Fincher)
* (`2a12cad <https://github.com/litestar-org/litestar-fullstack/commit/2a12cada9d8b0fd173c962309aa2644271e3e323>`_)  - Reference library version as default openapi version (Cody Fincher)
* (`e460d5d <https://github.com/litestar-org/litestar-fullstack/commit/e460d5db45e6b973accda9aea218910923ab5c79>`_)  - Additional deprecation changes (Cody Fincher)
* (`c683d30 <https://github.com/litestar-org/litestar-fullstack/commit/c683d30281a938cea7550e0084d3d96d61b2d59c>`_)  - Updated signature namespace (Cody Fincher)
* (`891e732 <https://github.com/litestar-org/litestar-fullstack/commit/891e7321254002c5af4d9a9b1590a85a9bd4e12b>`_)  - Docker compose shell command (#40) (Faolain)
* (`5fcc4e2 <https://github.com/litestar-org/litestar-fullstack/commit/5fcc4e2be51b1289fe2f5f234b0b215c438f9734>`_)  - Handle breaking change from middleware updates to litestar (#44) (Faolain)
* (`a755dd0 <https://github.com/litestar-org/litestar-fullstack/commit/a755dd0cbe5c6fb9ac3f1a50613c7e86181c4734>`_)  - Update pre-commit, remove re2 (Cody Fincher)
* (`9b6c38e <https://github.com/litestar-org/litestar-fullstack/commit/9b6c38edfaadecc52e179497d7c16cf57d8c7cc0>`_)  - Remove `mypy.ini` reference from Dockerfile (Cody Fincher)
* (`2be7ac7 <https://github.com/litestar-org/litestar-fullstack/commit/2be7ac7aaf23293ea064edd7970db7ab39d30bfd>`_)  - Update copy-pasted description of the `reset-database` CLI command (#47) (0xSwego), Co-authored-by:0xSwego <OxSwego@gmail.com>
* (`7a2f79c <https://github.com/litestar-org/litestar-fullstack/commit/7a2f79c00d8c940de9a9b2720edd9b6db4122af3>`_)  - Update `cp .env` command in documentation (#46) (0xSwego), Co-authored-by:0xSwego <OxSwego@gmail.com>
* (`eeec275 <https://github.com/litestar-org/litestar-fullstack/commit/eeec275c135d6db41d203ac5742b6fdb4286ccb0>`_)  - Use built in auto-commit handler (#63) (Cody Fincher)
* (`5d57a00 <https://github.com/litestar-org/litestar-fullstack/commit/5d57a00bcddf7d3c986a2f852ad78cb9063e498d>`_)  - Make sure sessions are closed in tests (#62) (0xSwego), Co-authored-by:0xSwego <OxSwego@gmail.com>
* (`ad118e8 <https://github.com/litestar-org/litestar-fullstack/commit/ad118e87439b433aeafac5edab84c0ec5d0207e1>`_)  - Cleanup tests and correct imports (#71) (Cody Fincher)
* (`d9aa54d <https://github.com/litestar-org/litestar-fullstack/commit/d9aa54d0520fd3020735dbe83de7356485214097>`_)  - Small typo using print (#79) (Manuel Sanchez Pinar)
* (`62733bd <https://github.com/litestar-org/litestar-fullstack/commit/62733bd7ed303105d4cca5b301710f54c964f989>`_)  - Correct `aiosql` import (#84) (Cody Fincher)
* (`64da7b7 <https://github.com/litestar-org/litestar-fullstack/commit/64da7b7477256200db8595649dc0352faa7fdf0f>`_)  - Update ``.env`` ``alembic.ini`` path (#86) (Jacob Coffee)
* (`f23d181 <https://github.com/litestar-org/litestar-fullstack/commit/f23d18173b6adbc36709b8a70aae4adc21465415>`_)  - Run async tests with `anyio` and `asyncio` backend (#89) (Franz)
* (`8a89fa1 <https://github.com/litestar-org/litestar-fullstack/commit/8a89fa11e9b48cd925f0352aad5f762740315282>`_)  - Handle default behaviour change in `CollectionFilter` for empty lists (#90) (Cody Fincher)
* (`6303474 <https://github.com/litestar-org/litestar-fullstack/commit/6303474563e452475916ba488fe48d74170c7c0c>`_)  - Updates for `AsyncCallable` changes (#94) (Cody Fincher)
* (`e188969 <https://github.com/litestar-org/litestar-fullstack/commit/e1889694de6ec37d068e1866c65a6f794bae8d89>`_)  - Adds anyio marker (#95) (Cody Fincher)
* (`492cec6 <https://github.com/litestar-org/litestar-fullstack/commit/492cec66b027bb36256350bfb8fc1e2248985c8c>`_)  - Add infrastructure checks for `redis` and `postgres` (#99) (Cody Fincher), Co-authored-by:Faolain <Faolain@users.noreply.github.com>

* feat: use `docker-compose` in test or by config

* feat: remove unused extra code

* chore: bump deps

---------, Co-authored-by:Kumzy <Kumzy@users.noreply.github.com>, Co-authored-by:Faolain <Faolain@users.noreply.github.com>

Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`9463734 <https://github.com/litestar-org/litestar-fullstack/commit/94637345ea19610e1ebd9b5a28024f704130558d>`_)  - Adds banner artwork for future updates (#61) (Cody Fincher)
* (`80ad7e4 <https://github.com/litestar-org/litestar-fullstack/commit/80ad7e432175a77ea2aceb99480fa06622e10e21>`_)  - Update README.md features (#68) (Tom V), Co-authored-by:Cody Fincher <204685+cofin@users.noreply.github.com>
* (`464043e <https://github.com/litestar-org/litestar-fullstack/commit/464043eb4315419caf3358096bfe38a9425e7cdd>`_)  - Fix pdm install command (#93) (Faolain)

FIX
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`5997f90 <https://github.com/litestar-org/litestar-fullstack/commit/5997f90314fb07f6d42e1bc756bcf32c413cf011>`_)  - Change 401 to 403 for insufficient privileges (#10) (Bäm)
* (`95f19b3 <https://github.com/litestar-org/litestar-fullstack/commit/95f19b3fb76da60d2d45b951ba7544288c22db30>`_)  - Fields for Before and After filters (#9) (Bäm)

Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`044e271 <https://github.com/litestar-org/litestar-fullstack/commit/044e271fcd299b02ff979b9beb10bbf341b80490>`_)  - Dynamically set the reload dir based on module path. (Cody Fincher)
* (`7259fc8 <https://github.com/litestar-org/litestar-fullstack/commit/7259fc8711959b22b8faa5a676d3135458a7ae92>`_)  - Launch worker in-process or as standalone with CLI flags. (Cody Fincher)
* (`5b2bdb7 <https://github.com/litestar-org/litestar-fullstack/commit/5b2bdb76f4a7b6fd917874513ae854fa2fca74d2>`_)  - Adds ruff integration (Cody Fincher)
* (`dfa670d <https://github.com/litestar-org/litestar-fullstack/commit/dfa670d7c3361162662e537a27281c6a9332e7f8>`_)  - Renamed background worker setting name (Cody Fincher)
* (`ca68c70 <https://github.com/litestar-org/litestar-fullstack/commit/ca68c70e7eb1f67b098a53a1d31f0920f3d0bed4>`_)  - Add slugify function (Cody Fincher)
* (`5d4a803 <https://github.com/litestar-org/litestar-fullstack/commit/5d4a80391d2dac739ca3312457522735bac83a26>`_)  - Argon2 crypt config (Cody Fincher)
* (`b559622 <https://github.com/litestar-org/litestar-fullstack/commit/b559622224e4ee5aee549b48963650f8a16d6e7e>`_)  - Security config (Cody Fincher)
* (`1a70320 <https://github.com/litestar-org/litestar-fullstack/commit/1a70320df6fdf499f30171db7c730bb75fdfbbfd>`_)  - Implement base of team domain (Cody Fincher)
* (`0a68149 <https://github.com/litestar-org/litestar-fullstack/commit/0a68149c05f40badb39c067e897c0cc9d805e2d6>`_)  - Additional updates for teams (Cody Fincher)
* (`f7ca0a0 <https://github.com/litestar-org/litestar-fullstack/commit/f7ca0a0d075335dc548d455a4aa04649d95924fa>`_)  - Adds CLI test case (Cody Fincher)
* (`f66df49 <https://github.com/litestar-org/litestar-fullstack/commit/f66df497e63b56969046f738b0939af5e0c5c358>`_)  - Updated uvicorn.run, added base schema, (Cody Fincher)
* (`28f3d78 <https://github.com/litestar-org/litestar-fullstack/commit/28f3d787678df464933010a7c34bb881263bccab>`_)  - Refactored user auth service (Cody Fincher)
* (`45d6d29 <https://github.com/litestar-org/litestar-fullstack/commit/45d6d29ab2a30d84ca6acfe5314b0f58307321f8>`_)  - Implements new command to start worker independently. (Cody Fincher)
* (`5a6a003 <https://github.com/litestar-org/litestar-fullstack/commit/5a6a003478019ba353e6a8fcd369b2525497b9b7>`_)  - Team guards (Cody Fincher)
* (`c679211 <https://github.com/litestar-org/litestar-fullstack/commit/c6792117ac74da074b5ed1fa3570da7a979f704b>`_)  - Adds HTMX library (Cody Fincher)
* (`571d81c <https://github.com/litestar-org/litestar-fullstack/commit/571d81c80637e2b732828e245681ea945abfb454>`_)  - Updated build process to also download wheels if needed (Cody Fincher)
* (`ea2d0eb <https://github.com/litestar-org/litestar-fullstack/commit/ea2d0ebdb6443a7d158d5e8919af9b0211d523e2>`_)  - Adds js for generating routes. adapted  from flask-inertia (Cody Fincher)
* (`4ee18d5 <https://github.com/litestar-org/litestar-fullstack/commit/4ee18d541ac94914872fa923b0e0da5e074cfe50>`_)  - Launches vite in a separate process (Cody Fincher)
* (`3edd174 <https://github.com/litestar-org/litestar-fullstack/commit/3edd174955fd6de6a76ca728b5a5f1e72590904b>`_)  - Moves to signature provider (Cody Fincher)
* (`f09c144 <https://github.com/litestar-org/litestar-fullstack/commit/f09c144ab39c98cddc43c9c841af2794f7593116>`_)  - Utilize the `ruff` and `pre-commit` configurations from `starlite` (Cody Fincher)
* (`3e4a4ad <https://github.com/litestar-org/litestar-fullstack/commit/3e4a4ad2b817058eba1f19e8e8339f990428c49a>`_)  - New controllers and commands (#8) (Cody Fincher), Features:- Adds `promote-to-superuser` management command.  This allows you to promote an existing user to a superuser from the command line: `poetry run app manage promote-to-superuser --email example@string.com`
  - Adds `create-user` management command to create users from the CLI.  `poetry run app manage create-user`
  - Adds User Account CRUD routes that require superuser access to utilize (promote your user with the above command to test)
  - Adds `created`,`updated` Audit columns to model and squashed migrations.  Please run `poetry run app manage reset-database` to reset your database with the latest DDL.
  - Adds base of Team, Team Member, and Team Invitation services.
* (`7ae8411 <https://github.com/litestar-org/litestar-fullstack/commit/7ae84116ab20ebe8dfe618b3ab314cfe9a523a01>`_)  - Adds exists and updated type check logic (Cody Fincher)
* (`5c5874b <https://github.com/litestar-org/litestar-fullstack/commit/5c5874bdd8139484015aeeed33b9e129fb12a654>`_)  - `litestar` rebrand (#11) (Cody Fincher), Co-authored-by:Cody Fincher <cody@gluent.com>
* (`b2b87d4 <https://github.com/litestar-org/litestar-fullstack/commit/b2b87d4a68fa5c6ca4a7a48752e83c2d816fd12d>`_)  - Team controller and service updates (#12) (Cody Fincher), Co-authored-by:Cody Fincher <cody@gluent.com>
* (`84a7b2b <https://github.com/litestar-org/litestar-fullstack/commit/84a7b2b21f072b246998d4313a3258728ff332ba>`_)  - Upgrade to Litestar alpha 5 & testing updates (#15) (Cody Fincher)
* (`95581da <https://github.com/litestar-org/litestar-fullstack/commit/95581dae96de6528224b38ed45c441bcd5f204bf>`_)  - Adds an example of integrating `aiosql`, `sqlalchemy` and `litestar` (#16) (Cody Fincher), Co-authored-by:Cody Fincher <cody.fincher@gmail.com>
* (`9547e93 <https://github.com/litestar-org/litestar-fullstack/commit/9547e93d8ec8c919ceaca828f5dbd3448c50f300>`_)  - Add additional association proxies (Cody Fincher)
* (`4167014 <https://github.com/litestar-org/litestar-fullstack/commit/4167014d76836adde626a16fedd064d69a2f5422>`_)  - Basic example of calling the litestar cli from another click app. (Cody Fincher)
* (`fccd306 <https://github.com/litestar-org/litestar-fullstack/commit/fccd30674eab65b908dba138e1de8c99f576f049>`_)  - Adds tests for crypt functions (Cody Fincher)
* (`fb666b2 <https://github.com/litestar-org/litestar-fullstack/commit/fb666b2921b625522c8bc3bcf5c64cb89df72e27>`_)  - Adds additional tests for user login (Cody Fincher)
* (`2ea42c0 <https://github.com/litestar-org/litestar-fullstack/commit/2ea42c0a2d4042a3e1d56810d9b29f344ecf66ba>`_)  - System health check endpoint and additional test. (Cody Fincher)
* (`615cb1d <https://github.com/litestar-org/litestar-fullstack/commit/615cb1d410c407e67755602411487f83209e7d7e>`_)  - Serves the SAQ UI through Litestar (#20) (Cody Fincher), Changelog:* fix: removes dict tracebacks that sometimes cause serializing issues

  * fix: linting changes

  * feat: updated worker pattern

  * feat: additional work on saq web UI integration

  * feat: re-implements saq UI in Litestar.

* (`9a419ee <https://github.com/litestar-org/litestar-fullstack/commit/9a419eec3ebcb57c287e0975571719693e38c9bb>`_)  - Makefile enhancements.  additional serializers in the msgspec handlers (Cody Fincher)
* (`d1d0ebf <https://github.com/litestar-org/litestar-fullstack/commit/d1d0ebfe8f2eda255d5a072903443a56e47a3c16>`_)  - Adds ability to have tasks and jobs available on different queues. (Cody Fincher)
* (`b1ed90b <https://github.com/litestar-org/litestar-fullstack/commit/b1ed90be54dd8c96d520452f56f93a7ba517f9d2>`_)  - Move saq to plugin (#34) (Cody Fincher)
* (`8701612 <https://github.com/litestar-org/litestar-fullstack/commit/8701612670205417cde095e01d9a81c774dccaec>`_)  - Adds `to_dto` method to service (Cody Fincher)
* (`c2a5e16 <https://github.com/litestar-org/litestar-fullstack/commit/c2a5e16c6e559eb61bb4b030e91a17922c60cb95>`_)  - App now uses litestar CLI (Cody Fincher)
* (`7037c83 <https://github.com/litestar-org/litestar-fullstack/commit/7037c8379a47df5ef7ce5ce655c5f347e70e5542>`_)  - Swap to main branch of litestar (Cody Fincher)
* (`661a266 <https://github.com/litestar-org/litestar-fullstack/commit/661a26690c61d6fb28347853049e7507b6d26ad1>`_)  - Add example of default sorts (Cody Fincher)
* (`bf3dc66 <https://github.com/litestar-org/litestar-fullstack/commit/bf3dc664414fc72148a3eb22b3624e0f39845ca2>`_)  - Adds example of many-to-many without association table. (Cody Fincher)
* (`eedd47b <https://github.com/litestar-org/litestar-fullstack/commit/eedd47b609fbe00d3f2a694e000fa41599f85655>`_)  - Moves to dto implementation. (#36) (Cody Fincher)
* (`959db41 <https://github.com/litestar-org/litestar-fullstack/commit/959db41333acde190c25e49869729a7abd01c978>`_)  - Docker build enhancements. (#37) (Cody Fincher)
* (`d5d85d8 <https://github.com/litestar-org/litestar-fullstack/commit/d5d85d8f799b135f62fd4c25902b36a219634448>`_)  - Enhanced migration template (Cody Fincher)
* (`478c7ef <https://github.com/litestar-org/litestar-fullstack/commit/478c7ef89f8ed9375aabe052b86af18de967f60c>`_)  - Implement batched alter statements (Cody Fincher)
* (`152cea7 <https://github.com/litestar-org/litestar-fullstack/commit/152cea77647951e14c444202ebbc2cea4f9a0b54>`_)  - Create `contrib` folder for easier management of plugins. (Cody Fincher)
* (`4466b82 <https://github.com/litestar-org/litestar-fullstack/commit/4466b8208f3eed6b7772bf8256d2093745988094>`_)  - Move vite into a plugin format (Cody Fincher)
* (`d0490d5 <https://github.com/litestar-org/litestar-fullstack/commit/d0490d55d274c12144949c1c61e92db5fb60525e>`_)  - Rudimentary Windows support (#39) (Ephedra), Co-authored-by:3phedra <v.w@mailbox.org>, Co-authored-by:Cody Fincher <cody.fincher@gmail.com>
* (`bf24bb3 <https://github.com/litestar-org/litestar-fullstack/commit/bf24bb3718e7052cd24ae59955f05af8c7ca25df>`_)  - Re-add imports (Cody Fincher)
* (`3185c95 <https://github.com/litestar-org/litestar-fullstack/commit/3185c955179a9e1f763426c1ec81683afc74f788>`_)  - Upgraded support for litestar 2.1.1 (#78) (Cody Fincher)
* (`6bf83ba <https://github.com/litestar-org/litestar-fullstack/commit/6bf83ba05f4800a989f37d34a8b3ec3138240295>`_)  - Enable Alembic CLI integration (#80) (Cody Fincher)
* (`01880bd <https://github.com/litestar-org/litestar-fullstack/commit/01880bdf10b06d4a342831a7be13c178de1bf57f>`_)  - Swap to `aiosql`, `vite`, and `saq` plugins (#82) (Cody Fincher)
* (`0587794 <https://github.com/litestar-org/litestar-fullstack/commit/0587794c3acc0e17ec4175fe3a5a9ea9e269e47f>`_)  - Move to `advanced_alchemy` services (#85) (Cody Fincher)
* (`df72846 <https://github.com/litestar-org/litestar-fullstack/commit/df72846a6258ca9ef2de9e7ff1ceae80679834c4>`_)  - Adds a custom entrypoint (#92) (Cody Fincher)
* (`64a2866 <https://github.com/litestar-org/litestar-fullstack/commit/64a286635533266efcc47cf715e95586e084f277>`_)  - Add version identifier for pdm, railway, rtx, etc. (Jacob Coffee)

Miscellaneous Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`05233d2 <https://github.com/litestar-org/litestar-fullstack/commit/05233d281f5a735b032c73d1d744e82efbdf0bcd>`_)  - Docstring cleanup. (Cody Fincher)
* (`111cbc3 <https://github.com/litestar-org/litestar-fullstack/commit/111cbc3f9419d609bdf084c947e3bf20d26e8a90>`_)  - Documentation update (Cody Fincher)
* (`6389a18 <https://github.com/litestar-org/litestar-fullstack/commit/6389a182f1178529184cbe5c15204d0872f76565>`_)  - Linting/repo cleanup (Cody Fincher)
* (`a12dc28 <https://github.com/litestar-org/litestar-fullstack/commit/a12dc28533fb11f5a30c4edbdb9265870a33eb0c>`_)  - Linting updates (Cody Fincher)
* (`d899658 <https://github.com/litestar-org/litestar-fullstack/commit/d899658e5d6a858a80ef65d8ef9e50d662c63fdd>`_)  - Linting updates (Cody Fincher)
* (`584ded7 <https://github.com/litestar-org/litestar-fullstack/commit/584ded72f13acfeb9163b684549e28fabbc811b2>`_)  - Linting updates (Cody Fincher)
* (`627021c <https://github.com/litestar-org/litestar-fullstack/commit/627021c2754e5ce83df5b092e0afe88f4d3c12ca>`_)  - Updated ruff config (Cody Fincher)
* (`e59748c <https://github.com/litestar-org/litestar-fullstack/commit/e59748c7866c85c1aa23af700487b5e41b0acac6>`_)  - Version bumps (Cody Fincher)
* (`7cdf5e0 <https://github.com/litestar-org/litestar-fullstack/commit/7cdf5e09d3fd26e0633dd286346cde024bdf7968>`_)  - Added additional note (Cody Fincher)
* (`486c0ca <https://github.com/litestar-org/litestar-fullstack/commit/486c0ca5ef36c47706a0d4df0a70ae5514ec3669>`_)  - Updated readme.md (Cody Fincher)
* (`fdf6fa1 <https://github.com/litestar-org/litestar-fullstack/commit/fdf6fa1020770dbca1bf23f3b7ab65b081ded0b2>`_)  - Add more to the readme (Cody Fincher)
* (`43eb065 <https://github.com/litestar-org/litestar-fullstack/commit/43eb06578cf49884518cfbe6b512e204d472624b>`_)  - Formatting (Cody Fincher)
* (`1c85258 <https://github.com/litestar-org/litestar-fullstack/commit/1c852588b076061ab71410aa345aa315ae6a44ac>`_)  - More formatting (Cody Fincher)
* (`9cd5d1f <https://github.com/litestar-org/litestar-fullstack/commit/9cd5d1f265f271365a61e36b1a6c3b7eb2b7d43a>`_)  - More updates (Cody Fincher)
* (`a82fbf5 <https://github.com/litestar-org/litestar-fullstack/commit/a82fbf5e7227650082d0dc30acd88c323d6af1a1>`_)  - Added additional notes and links (Cody Fincher)
* (`825b168 <https://github.com/litestar-org/litestar-fullstack/commit/825b168eac86c893eaeb49af3698fa5ef46f9744>`_)  - Version bumps (Cody Fincher)
* (`4e00391 <https://github.com/litestar-org/litestar-fullstack/commit/4e00391c99128ce05f7fbc7c73f3f43edc935f8a>`_)  - Linting updates (Cody Fincher)
* (`d38039a <https://github.com/litestar-org/litestar-fullstack/commit/d38039a23efe65db3f4f2a76441f0b619d69c1e2>`_)  - Lint/version bumps (Cody Fincher)
* (`046592e <https://github.com/litestar-org/litestar-fullstack/commit/046592ece2abe69c7dd66f6757cd9bd49c4f6e17>`_)  - Version bump (Cody Fincher)
* (`691770d <https://github.com/litestar-org/litestar-fullstack/commit/691770d56f23001f140098f09ef0727bac594b4a>`_)  - Upgrade to beta4 (Cody Fincher)
* (`f8baaa6 <https://github.com/litestar-org/litestar-fullstack/commit/f8baaa69a719f8a02e0fe4ebf9dcebec335712a5>`_)  - Bump actions/checkout from 3 to 4 (dependabot[bot]), Signed-off-by:dependabot[bot] <support@github.com>
* (`fc91c18 <https://github.com/litestar-org/litestar-fullstack/commit/fc91c18af7acd97f8c4e79169739caa86d30a967>`_)  - Migrate to PDM (#81) (Cody Fincher)
* (`649cbdd <https://github.com/litestar-org/litestar-fullstack/commit/649cbddb2537bd41126f8c40227438cc57261ebf>`_)  - Align license with litestar-org (#83) (Cody Fincher)
* (`06c0b5f <https://github.com/litestar-org/litestar-fullstack/commit/06c0b5f2e19d08fac76a1a8c1542d75e2385c167>`_)  - Correct container build issues (#87) (Cody Fincher), fix:address build issues and move to the latest litestar (#87)

Testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`074f8ba <https://github.com/litestar-org/litestar-fullstack/commit/074f8ba736bab7c59232c5f7d28280d8b6ef5749>`_)  - Remove pytest docker and replace with custom implementation (Cody Fincher)

Ci
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`b4ae5ee <https://github.com/litestar-org/litestar-fullstack/commit/b4ae5eef21b1de8a5a216dc7561133643ea66fcd>`_)  - Move mypy config to pyproject.toml.  Address deprecated import (Cody Fincher)
* (`1b91b05 <https://github.com/litestar-org/litestar-fullstack/commit/1b91b053a46a64d332e51b4c81c9f9c9b527d5ea>`_)  - Apply pre-commit (Jacob Coffee)
* (`45f7a09 <https://github.com/litestar-org/litestar-fullstack/commit/45f7a0983c735d87a3616a032d2d28bcb07c36b9>`_)  - Fix badges (Jacob Coffee)
* (`f11fdc4 <https://github.com/litestar-org/litestar-fullstack/commit/f11fdc4d38a2ee04059642d3b66c865ce5c8dd16>`_)  - Fix badges (Jacob Coffee)

Infra
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`42a8f66 <https://github.com/litestar-org/litestar-fullstack/commit/42a8f6623f8fdfbed02682a69658415b61fe3dbf>`_)  - Set host to `0.0.0.0` instead of `127.0.0.1`.  This enables external access to the container. (#60) (Cody Fincher)
* (`39ba71b <https://github.com/litestar-org/litestar-fullstack/commit/39ba71b665784a3a768d8f1c4e1f0d779fab15b7>`_)  - Fix `source` not found on some shells (#64) (Cody Fincher)
* (`0ef30d7 <https://github.com/litestar-org/litestar-fullstack/commit/0ef30d73d4c5622ce2da94b882ba82935b0c284e>`_)  - Adds docker compose for running redis, db, mailhog only (#65) (Cody Fincher)

Meta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`9a84690 <https://github.com/litestar-org/litestar-fullstack/commit/9a84690bb40d8c9324579c08d5df55f74e609e03>`_)  - Org updates (#72) (Jacob Coffee)

Wip
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* (`84af1da <https://github.com/litestar-org/litestar-fullstack/commit/84af1da3837ee8ad11cfa904e651a18cdc751614>`_)  - Begin refactoring for 2.0 (Cody Fincher)

Litestar Fullstack Changelog
