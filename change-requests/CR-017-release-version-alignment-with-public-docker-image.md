---
title: "Align release version with docker-publish.yml tag strategy on Google Artifact Registry"
status: applied
author: "roberto"
created-at: "2026-03-19T00:00:00.000Z"
---

# CR-017: Align Release Version with docker-publish.yml Tag Strategy

## Summary

Define and enforce a single release version identifier across:

1. Git repository release/tag metadata
2. Docker image tags produced by `.github/workflows/docker-publish.yml` and pushed to Google Artifact Registry

This allows users to subscribe to release/image notifications and immediately identify which GAR image tag to pull and deploy.

## Problem Analysis

The repository already publishes backend/frontend images via `.github/workflows/docker-publish.yml` to GAR:

- `${REGISTRY}/${PROJECT_ID}/${GAR_REPOSITORY}/${IMAGE_NAME_BACKEND}`
- `${REGISTRY}/${PROJECT_ID}/${GAR_REPOSITORY}/${IMAGE_NAME_FRONTEND}`

Current metadata tags are `latest` and `rev-<short_sha>`. The workflow also exposes `workflow_dispatch.inputs.image_tag`, but this value is not currently used in metadata/tag generation. Because of this mismatch, users face:

1. Ambiguity about which image corresponds to a release.
2. Harder upgrade communication across changelog, docs, and deployment instructions.
3. Reduced usefulness of notification channels (GitHub Releases watch, registry tag updates) because versions are not consistently mapped.
4. Higher risk of deploying a wrong image tag.

## Goals

1. One canonical version source for every publish event.
2. Same version string used in release communication and in GAR image tags.
3. Public and documented upgrade path for users.
4. Reliable notification points when new versions are published.

## Proposed Solution

Adopt a version contract that is explicitly tied to `docker-publish.yml` execution context.

1. Compute a canonical `VERSION` in workflow using this precedence:
   - `workflow_dispatch.inputs.image_tag` when provided
   - `github.ref_name` when event is a git tag (`v*`)
   - `rev-<short_sha>` fallback for branch builds
2. Pipeline builds and publishes backend/frontend images with `${VERSION}`.
3. Keep `latest` as optional convenience tag for stable release events only.
4. Release notes (or publish summary) include exact GAR image references using the same `${VERSION}`.
5. Product docs explain how users can subscribe to updates:
   - GitHub Releases watch
   - GAR/repository tag notifications where available

## Requirements

### Functional requirements

1. Version source must be derived from `docker-publish.yml` context with explicit precedence (manual input -> git tag -> `rev-<sha>`).
2. On publish, both backend and frontend images must include the same `${VERSION}` tag in GAR.
3. For git tag releases (`v*`), release communication must use the same tag as image version.
4. Publish job must fail if backend/frontend tags diverge from computed `${VERSION}`.
5. Release notes template must include:
   - version
   - GAR image names and tags
   - pull examples
   - upgrade notes
6. Existing branch/PR workflow continues to support non-release images via `rev-<sha>` without changing release semantics.
7. Public documentation must include version-to-image mapping rules.

### Non-functional requirements

1. Tags must be deterministic and reproducible.
2. No credentials leakage in CI logs.
3. Release and image publication should be idempotent on rerun.
4. Rollback should be possible by redeploying a prior `${VERSION}` tag from GAR.

## Versioning Policy

1. For release tags, semantic versioning with `v` prefix remains supported (`vMAJOR.MINOR.PATCH`).
2. The canonical publish version is the workflow-computed `${VERSION}` and must be applied to both images.
3. Optional `latest` must point only to approved stable release publishes.
4. Pre-releases (`vX.Y.Z-rc.N`) are allowed only when explicitly provided as `${VERSION}`.

## Changes Required

### CI/CD

1. Update `.github/workflows/docker-publish.yml` to:
   - compute a reusable `${VERSION}` value
   - inject `${VERSION}` into `docker/metadata-action` tags for backend and frontend
   - ensure `workflow_dispatch.inputs.image_tag` is actually used
2. Add consistency check step:
   - verify generated image tags contain exactly `${VERSION}` for both images
   - verify release notes/publish summary contain GAR references with `${VERSION}`

### Documentation

1. Update `system/ci-pipeline.md` with docker-publish version contract and precedence rules.
2. Update `system/architecture.md` with artifact/version flow.
3. Update `product/features/docker-images-deployment.md` with user-facing pull/upgrade examples.
4. Add "How to get notified" section (Releases watch + registry notifications where supported).

### Optional CLI enhancement

1. Add a command/help note (for example in deploy docs) to check latest published GAR `${VERSION}` and compare it with running version.

## Implementation Plan

1. Define and implement `${VERSION}` computation in `docker-publish.yml`.
2. Wire `${VERSION}` into backend/frontend metadata tags.
3. Keep `rev-<sha>` for branch builds and add release tag mapping for `v*` events.
4. Optionally gate `latest` to stable release events.
5. Add automated assertions that both images receive identical `${VERSION}`.
6. Update release notes/publish summary template with GAR references.
7. Update deployment and notification documentation.
8. Run a dry-run publish and then release with a real `vX.Y.Z` tag.

## Acceptance Criteria

1. Running `docker-publish.yml` produces one canonical `${VERSION}` for the run.
2. Backend and frontend images are published to GAR with identical `${VERSION}` tag.
3. For release tags (`v*`), the same version appears in release communication and image references.
4. Users can identify upgrade target from one version string only.
5. Non-release builds remain supported via `rev-<sha>` tags.
6. CI prevents publish success when backend/frontend version mismatch occurs.

## Risks and Mitigations

- Risk: manual `image_tag` override is inconsistent with git tag.
   - Mitigation: validate and fail when manual override conflicts with tag-event ref.

- Risk: `latest` tag drift causes confusion.
   - Mitigation: document `latest` policy and keep `${VERSION}` as canonical reference.

- Risk: partial failure (image published, release not created).
  - Mitigation: add retry/idempotent steps and a consistency check job.

- Risk: GAR repository visibility/notification behavior varies by organization settings.
   - Mitigation: make GitHub Releases the mandatory notification channel; GAR notifications are optional.

## Rollout Notes

1. Start with one pilot release tag (for example `v0.1.0`) using the updated workflow.
2. Verify GAR image tags and release notes consistency.
3. Announce notification instructions in README and release notes.
4. Use workflow `${VERSION}` as the production deploy reference (semver for official releases).
