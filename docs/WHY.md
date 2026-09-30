# Why it's built this way

## The problem

A variant a researcher cares about is often not on the array a participant was genotyped on. A
nearby variant in perfect linkage disequilibrium can stand in for it, but only if you find the right
proxy, filter out the untrustworthy ones, and check which participants actually have it typed.

## Design choices

**Why read LDproxy columns by header name?** Because the response has extra annotation columns, and
a position-based parser silently reads the wrong field if a column is added or moved. The original
version never parsed distance at all; reading by name made that obvious and easy to fix.

**Why drop the query variant's own row?** Because LDproxy lists the target first with R² 1.0. If it
counts as a proxy, every target appears to have at least one perfect proxy, which hides exactly the
cases that need attention.

**Why default to R² = 1.0?** Because a recall is a decision about individual people. At R² 0.9 some
participants are placed in the wrong genotype group. A lower threshold is available, but it has to
be chosen on purpose.

**Why record which variant provides the data?** Because "available: Yes" is not actionable. The
person extracting or re-genotyping needs the rsID, and the audit trail needs it too.

**Why return errors instead of raising in batch queries?** Because one unknown rsID should not
abort a long list. Every failure is still visible in `ProxyResult.error`, so nothing is lost
silently.

**Why no dependencies beyond the standard library?** Because research compute environments are
often locked down, and `urllib` plus `csv` is enough for this job.

## Questions worth asking

**"R² = 1.0 in 1000 Genomes GBR. Why should I trust it in your cohort?"**
You should not, without checking. The reference panel is small and may not match the cohort's
ancestry mix. Where some participants have both target and proxy typed, measure concordance before
using the proxy for anyone else. That check is on the roadmap; today it is a documented limitation.

**"Availability is not genotype. How do you get from the proxy genotype to the target genotype?"**
Through the allele pairing LDproxy reports (`Correlated_Alleles`, kept on each `ProxyVariant`),
after aligning strand and alleles to the array. This repo stops at availability on purpose: getting
allele alignment wrong flips genotype groups, so it belongs in a step that is tested against typed
data.

**"What if the participant file uses array probe IDs rather than rsIDs?"**
Then it has to be mapped to rsIDs first, using the array manifest and a fixed dbSNP build. Matching
here is by rsID string, so merged or renamed rsIDs are missed. The fix is to normalise identifiers
before mapping, not to add fuzzy matching.

## What's next

- Cache LDproxy responses on disk so repeated requests do not hit the API.
- Add a concordance check for target-proxy pairs where both are typed.
- Add a small CLI so the workflow runs without writing Python.
