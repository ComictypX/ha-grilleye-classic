"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const publish = require("../../.github/scripts/release.cjs");

function setup() {
  const calls = [];
  const missing = () => { throw Object.assign(new Error("Not found"), {status: 404}); };
  const config = {
    calls,
    core: {info() {}},
    context: {repo: {owner: "test-owner", repo: "test-repo"}, ref: "refs/heads/main", eventName: "push", sha: "tested-sha"},
    readFile: path => path.endsWith("manifest.json")
      ? JSON.stringify({version: "0.2.0"})
      : "# Änderungen\n\n## 0.2.0\n\n- Six probes and alarms\n\n## 0.1.0\n\n- Old changes\n",
    github: {rest: {
      git: {getRef: async ({ref}) => ref === "heads/main" ? {data: {object: {sha: "tested-sha"}}} : missing()},
      repos: {
        getReleaseByTag: async () => missing(),
        createRelease: async data => { calls.push(data); return {data: {html_url: "https://example.com/release"}}; },
      },
    }},
  };
  return config;
}

test("publishes stable version at the exact tested commit with current changelog only", async () => {
  const config = setup();
  await publish(config);
  assert.equal(config.calls.length, 1);
  const release = config.calls[0];
  assert.equal(release.tag_name, "v0.2.0");
  assert.equal(release.target_commitish, "tested-sha");
  assert.equal(release.draft, false);
  assert.equal(release.prerelease, false);
  assert.equal(release.make_latest, "true");
  assert.match(release.body, /Six probes and alarms/);
  assert.doesNotMatch(release.body, /Old changes/);
  assert.match(release.body, /blob\/v0\.2\.0\/docs\/ALARMS.md/);
});

for (const [ref, eventName] of [["refs/heads/topic", "push"], ["refs/heads/main", "pull_request"], ["refs/tags/v0.2.0", "push"]]) {
  test(`rejects release from ${ref} / ${eventName}`, async () => {
    const config = setup();
    Object.assign(config.context, {ref, eventName});
    await assert.rejects(publish(config), /only be published from main/);
    assert.equal(config.calls.length, 0);
  });
}

test("manual main retry is supported", async () => {
  const config = setup();
  config.context.eventName = "workflow_dispatch";
  await publish(config);
  assert.equal(config.calls.length, 1);
});

test("does not publish a superseded main commit", async () => {
  const config = setup();
  config.github.rest.git.getRef = async () => ({data: {object: {sha: "newer-sha"}}});
  await publish(config);
  assert.equal(config.calls.length, 0);
});

test("does not overwrite an already published version", async () => {
  const config = setup();
  config.github.rest.repos.getReleaseByTag = async () => ({data: {draft: false, prerelease: false}});
  await publish(config);
  assert.equal(config.calls.length, 0);
});

test("does not silently replace a draft or prerelease", async () => {
  for (const data of [{draft: true}, {prerelease: true}]) {
    const config = setup();
    config.github.rest.repos.getReleaseByTag = async () => ({data});
    await assert.rejects(publish(config), /draft\/prerelease/);
    assert.equal(config.calls.length, 0);
  }
});

test("a pre-existing tag without release blocks publishing", async () => {
  const config = setup();
  config.github.rest.git.getRef = async () => ({data: {object: {sha: "tested-sha"}}});
  await assert.rejects(publish(config), /exists without a release/);
  assert.equal(config.calls.length, 0);
});

test("API permission errors are not mistaken for missing releases", async () => {
  const config = setup();
  config.github.rest.repos.getReleaseByTag = async () => { throw Object.assign(new Error("Forbidden"), {status: 403}); };
  await assert.rejects(publish(config), /Forbidden/);
  assert.equal(config.calls.length, 0);
});

test("invalid version or missing release notes block publication", async () => {
  for (const version of ["v0.2.0", "0.2.0-beta", "01.2.0", "0.2.1"]) {
    const config = setup();
    const original = config.readFile;
    config.readFile = path => path.endsWith("manifest.json") ? JSON.stringify({version}) : original(path);
    await assert.rejects(publish(config));
    assert.equal(config.calls.length, 0);
  }
});
