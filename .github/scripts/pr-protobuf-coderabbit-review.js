// Triggers a protobuf-driven CodeRabbit full review for PRs.

const fs = require("fs");

const MARKER_PREFIX = "<!-- CodeRabbit Protobuf Review Trigger:";
const MAX_COMMENTS_TO_SCAN = 500;
const MAX_FILES_TO_LIST = 80;
const MAX_DIFF_CHARS = 12000;

function readTextFileOrEmpty(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return "";
  }

  return fs.readFileSync(filePath, "utf8");
}

function parseUniqueLines(text) {
  const seen = new Set();
  const lines = [];

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || seen.has(line)) {
      continue;
    }
    seen.add(line);
    lines.push(line);
  }

  return lines;
}

function truncateDiff(diffText, maxChars = MAX_DIFF_CHARS) {
  if (diffText.length <= maxChars) {
    return {
      truncated: false,
      text: diffText,
    };
  }

  const slice = diffText.slice(0, maxChars);
  const lineBreakIndex = slice.lastIndexOf("\n");
  const safeSlice = lineBreakIndex > 0 ? slice.slice(0, lineBreakIndex) : slice;

  return {
    truncated: true,
    text: `${safeSlice}\n... (diff truncated in CI comment)`,
  };
}

async function hasExistingTriggerComment(github, owner, repo, issueNumber, marker) {
  try {
    const iterator = github.paginate.iterator(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issueNumber,
      per_page: 100,
    });

    let scanned = 0;
    for await (const { data: page } of iterator) {
      for (const comment of page) {
        scanned += 1;
        if (typeof comment?.body === "string" && comment.body.includes(marker)) {
          return true;
        }
        if (scanned >= MAX_COMMENTS_TO_SCAN) {
          // Scan is intentionally bounded. Prefer fail-closed to avoid duplicate trigger comments.
          return true;
        }
      }
    }
  } catch (error) {
    console.log("Failed while checking existing protobuf trigger comments:", {
      message: error?.message,
      status: error?.status,
      owner,
      repo,
      issueNumber,
    });
    // On API errors, fail-closed to avoid posting duplicate trigger comments.
    return true;
  }

  return false;
}

function buildCommentBody({
  marker,
  baseSha,
  headSha,
  changedFiles,
  diffSnippet,
  truncated,
  scopeMode,
  scopeReason,
  validationStatus,
  validationChecks,
}) {
  const fileLines = changedFiles
    .slice(0, MAX_FILES_TO_LIST)
    .map((filePath) => `- \`${filePath}\``);

  const hiddenCount = Math.max(0, changedFiles.length - MAX_FILES_TO_LIST);

  const fileList = fileLines.length > 0
    ? fileLines.join("\n")
    : "- (no .proto files changed in this PR)";

  const hiddenLine = hiddenCount > 0 ? `\n- ...and ${hiddenCount} more files` : "";

  const truncatedSuffix = truncated ? " (truncated)" : "";

  const diffSection = diffSnippet.trim()
    ? `
Protobuf contract diff excerpt${truncatedSuffix}:
\`\`\`diff
${diffSnippet}
\`\`\`
`
    : `
No .proto diff was detected for this head commit.
`;

  const checks = validationChecks.length > 0
    ? validationChecks
    : [
      "buf lint",
      "buf breaking --against \".git#ref=origin/main\"",
      "buf build",
    ];

  const validationSummary = validationStatus === "skipped"
    ? `Protobuf contract validation was intentionally skipped for this pull request.

Reason:
- No protobuf-impacting files changed, so buf lint/breaking/build were not required.`
    : `Protobuf contract validation passed for this pull request.

Validation checks passed:
${checks.map((check) => `- \`${check}\``).join("\n")}`;

  const reviewFocus = validationStatus === "skipped"
    ? `Please perform a full review for this PR.

Protobuf contract gate was skipped intentionally for this head commit because no protobuf-impacting files changed.
If you identify code changes that implicitly alter protobuf contracts, flag them explicitly.`
    : `Please review this PR with a protobuf-first contract focus:
- PR changes must comply with protobuf compatibility rules.
- Do not allow field renumbering/reuse, enum value reuse, or incompatible type changes.
- Flag package/service renames unless accompanied by a migration strategy.
- Verify generated protobuf artifacts and application logic align with updated message/service definitions.`;

  return `${marker}
@coderabbitai full review

${validationSummary}

- Base commit: \`${baseSha}\`
- Head commit: \`${headSha}\`
- Changed .proto files: ${changedFiles.length}
- Scope mode: \`${scopeMode}\`
${scopeReason ? `- Scope detail: ${scopeReason}\n` : ""}

${reviewFocus}

Changed .proto files:
${fileList}${hiddenLine}
${diffSection}
`;
}

async function createTriggerComment(github, owner, repo, issueNumber, body) {
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: issueNumber,
    body,
  });
}

async function main({ github, context }) {
  const { owner, repo } = context.repo;
  const prNumber = context.payload?.pull_request?.number;

  if (!prNumber) {
    console.log("No pull request found in payload. Skipping.");
    return;
  }

  const baseSha = process.env.BASE_SHA || "";
  const headSha = process.env.HEAD_SHA || "";
  const diffPath = process.env.PROTOBUF_DIFF_PATH || "";
  const filesPath = process.env.PROTOBUF_FILES_PATH || "";
  const scopeMode = process.env.PROTOBUF_SCOPE_MODE || "full";
  const scopeReason = process.env.PROTOBUF_SCOPE_REASON || "";
  const validationStatus = process.env.PROTOBUF_VALIDATION_STATUS || "passed";
  const validationChecks = parseUniqueLines((process.env.PROTOBUF_VALIDATION_CHECKS || "").replace(/,/g, "\n"));
  const isDryRun = (process.env.DRY_RUN || "false").toLowerCase() === "true";

  if (!baseSha || !headSha || !filesPath) {
    console.log("Missing required environment values. Skipping protobuf review trigger.", {
      hasBaseSha: Boolean(baseSha),
      hasHeadSha: Boolean(headSha),
      hasFilesPath: Boolean(filesPath),
    });
    return;
  }

  const fullDiff = readTextFileOrEmpty(diffPath);
  const changedFiles = parseUniqueLines(readTextFileOrEmpty(filesPath));
  const { text: diffSnippet, truncated } = truncateDiff(fullDiff, MAX_DIFF_CHARS);
  const marker = `${MARKER_PREFIX} ${headSha} -->`;

  if (await hasExistingTriggerComment(github, owner, repo, prNumber, marker)) {
    console.log(`CodeRabbit protobuf trigger already posted for PR #${prNumber} and head ${headSha}.`);
    return;
  }

  const body = buildCommentBody({
    marker,
    baseSha,
    headSha,
    changedFiles,
    diffSnippet,
    truncated,
    scopeMode,
    scopeReason,
    validationStatus,
    validationChecks,
  });

  if (isDryRun) {
    console.log(`[DRY RUN] Would create protobuf-triggered CodeRabbit comment for PR #${prNumber}.`);
    return;
  }

  try {
    await createTriggerComment(github, owner, repo, prNumber, body);
    console.log(`Posted protobuf-triggered CodeRabbit review comment on PR #${prNumber}.`);
  } catch (error) {
    if (error?.status === 403 || error?.status === 404) {
      console.log("Insufficient permissions to create PR comment in this context. Skipping.", {
        status: error?.status,
        owner,
        repo,
        prNumber,
      });
      return;
    }
    throw error;
  }
}

module.exports = main;
module.exports.hasExistingTriggerComment = hasExistingTriggerComment;
