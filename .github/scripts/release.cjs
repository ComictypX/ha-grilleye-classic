"use strict";

const fs = require("node:fs");

module.exports = async function publishRelease({github, context, core, readFile = fs.readFileSync}) {
  if (context.ref !== "refs/heads/main" || !["push", "workflow_dispatch"].includes(context.eventName)) {
    throw new Error("Releases may only be published from main after validation");
  }
  const manifest = JSON.parse(readFile("custom_components/grilleye_classic/manifest.json", "utf8"));
  const version = manifest.version;
  if (typeof version !== "string" || !/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) {
    throw new Error("A stable major.minor.patch manifest version is required");
  }
  const changelog = readFile("CHANGELOG.md", "utf8").replace(/\r\n/g, "\n");
  const section = changelog.split(/^## /m).find(text => text.startsWith(`${version}\n`));
  const notes = section?.slice(version.length).trim();
  if (!notes) throw new Error(`Missing changelog entry for ${version}`);

  const repo = context.repo;
  const head = await github.rest.git.getRef({...repo, ref: "heads/main"});
  if (head.data.object.sha !== context.sha) {
    core.info("A newer main commit exists; this older run will not publish");
    return;
  }
  const tag = `v${version}`;
  let existing;
  try {
    existing = (await github.rest.repos.getReleaseByTag({...repo, tag})).data;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  if (existing) {
    if (existing.draft || existing.prerelease) throw new Error(`Release ${tag} already exists as draft/prerelease`);
    core.info(`Release ${tag} is already published; it will not be changed`);
    return;
  }
  // Never attach a new release to an unrelated, pre-existing tag.
  let tagExists = false;
  try {
    await github.rest.git.getRef({...repo, ref: `tags/${tag}`});
    tagExists = true;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  if (tagExists) throw new Error(`Tag ${tag} exists without a release; inspect it before publishing`);

  const base = `https://github.com/${repo.owner}/${repo.repo}`;
  const body = `## Änderungen\n\n${notes}\n\n` +
    "## Installation\n\nIn HACS auf diese Version aktualisieren und Home Assistant neu starten. " +
    "Die vorhandene GrillEye-Integration nicht löschen.\n\n" +
    `Die Alarmvorlage muss separat importiert werden: [Anleitung](${base}/blob/${tag}/docs/ALARMS.md).\n\n` +
    "Alle Softwareprüfungen dieser Version sind bestanden. Funk, Fühlerabziehen und echte " +
    "iPhone-Push-Zustellung müssen praktisch getestet werden. Alarme ersetzen keine Grillaufsicht.";
  const result = await github.rest.repos.createRelease({
    ...repo, tag_name: tag, target_commitish: context.sha, name: tag, body,
    draft: false, prerelease: false, make_latest: "true",
  });
  core.info(`Published ${result.data.html_url}`);
};
