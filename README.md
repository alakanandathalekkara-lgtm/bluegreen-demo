# Jenkins blue-green deployment pipeline

Each build deploys a new version to the idle color (blue or green), smoke-tests it,
then switches nginx traffic to it. The old color keeps running, so rollback is instant.

## Stages
1. Checkout
2. Build image: `bg-app:$BUILD_NUMBER`
3. Deploy to idle color: runs the new container beside the live one
4. Smoke tests: `/health` returns UP and `/` shows the new version
5. Switch traffic: nginx `bg-router` is pointed at the new color and reloaded
6. Verify live traffic: `curl` through the router
7. Rollback (runs only on failure): restores the previous color and removes the failed container

## Testing the rollback
Run **Build with Parameters** with `BREAK_RELEASE` ticked. The release's `/health`
returns 500, smoke tests fail, and traffic stays on the old version.

## Run history
| Build | Result | Live version |
|---|---|---|
| 1 | Green | blue v1 |
| 2 | Green | green v2 |
| 3 | Red (broken release, rolled back) | green v2 |
| 4 | Green | blue v4 |
