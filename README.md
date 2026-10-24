# GHSA-c9cx-7r7m-264v — InvoiceShelf cross-tenant privilege escalation

> A company owner can place an attacker-controlled account into another tenant with an arbitrary role, including `owner`.

[Português do Brasil](README.pt-BR.md) · [Official advisory](https://github.com/InvoiceShelf/InvoiceShelf/security/advisories/GHSA-c9cx-7r7m-264v) · [Fix for 2.x](https://github.com/InvoiceShelf/InvoiceShelf/pull/826) · [Fix for 3.x](https://github.com/InvoiceShelf/InvoiceShelf/pull/822)

VulDB tracking: [submission #1028117](https://vuldb.com/submit/1028117) — analysis pending, CVE requested.

## At a glance

| Item | Value |
|---|---|
| Product | InvoiceShelf |
| Product repository | [`InvoiceShelf/InvoiceShelf`](https://github.com/InvoiceShelf/InvoiceShelf) |
| Affected | `<= 2.4.3`; `3.0.0-alpha.1` through `3.0.0-alpha.3` |
| Fixed | `2.4.4`; `3.0.0-alpha.4` |
| Severity | Critical |
| Weakness | CWE-284, CWE-863 |
| Suggested CVSS v3.1 | `9.1 — CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H` |
| Advisory | `GHSA-c9cx-7r7m-264v` |
| CVE | No known CVE at publication time |

## Why this happens

### Technical targets

| Item | Value |
|---|---|
| Endpoint | `POST /api/v1/members` and the corresponding member update route |
| Authorization context | Active tenant selected by the `company` request header |
| Attacker-controlled parameters | `companies[].id` and `companies[].role` |
| Validation | `app/Domains/Accounts/Http/Requests/MemberRequest.php::rules()` |
| Write path | `app/Domains/Accounts/Application/MemberService.php::create()` / `update()` |
| Controller | `app/Domains/Accounts/Http/Controllers/Company/MembersController.php` |

`MemberRequest` validates only the shape of the client-controlled `companies` array. It does not establish that the caller owns the referenced company or may assign the requested role:

```php
'companies' => ['required'],
'companies.*.id' => ['required'],
'companies.*.role' => ['required'],
```

`MemberService::create()` and `update()` then treat that list as authoritative. They synchronize memberships using the supplied IDs and switch Bouncer's authorization scope to each supplied company before assigning the supplied role:

```php
$member->companies()->sync($memberships->pluck('id'));

foreach ($memberships as $membership) {
    BouncerFacade::scope()->to($membership['id']);
    BouncerFacade::sync($member)->roles([$membership['role']]);
}
```

The controller verifies that the caller owns the active company. It does not bind that authorization decision to `companies[].id` in the request body. This creates a confused authorization boundary:

```text
owner of Company A
        │ authorized to create a member in A
        ▼
POST /api/v1/members
companies[0].id = Company B
companies[0].role = owner
        │ values trusted by the service
        ▼
attacker-controlled account becomes an owner of Company B
```

## Proof of concept

The repository deliberately provides a laboratory-only reproducer. It refuses non-loopback targets and does nothing unless `--execute` is supplied. We did not execute it while preparing this disclosure.

Prerequisites:

1. An isolated InvoiceShelf `2.4.3` or `3.0.0-alpha.3` test installation.
2. Two test companies, A and B.
3. A valid Sanctum token for an owner of Company A.
4. The numeric identifier of Company B.

Preview the request without sending it:

```bash
python3 poc/poc.py \
  --base-url http://127.0.0.1:8080 \
  --token LAB_TOKEN \
  --active-company-id 1 \
  --victim-company-id 2 \
  --email poc-user@example.invalid
```

After reviewing the generated request, an authorized tester can add `--execute`. On a vulnerable release, the expected vulnerable result is HTTP `200`/`201` and a new member associated with Company B as `owner`. A fixed release must reject the cross-company membership, normally with HTTP `403` or `422`, and must not create the unauthorized relationship.

See [poc/poc.py](poc/poc.py) and [poc/request.http](poc/request.http).

## Impact

An owner of one legitimate tenant can obtain administrative control over another tenant on the same installation. The resulting account can access or alter invoices, customers, payments and other financial records, invite additional users, and exercise any capability granted to the selected role. Confidentiality, integrity and availability cross the intended tenant boundary.

## Remediation

Upgrade to `2.4.4`, `3.0.0-alpha.4`, or a later release. The fix restricts submitted company IDs to companies owned by the caller, validates roles in their company scope, preserves memberships outside the caller's authority, and prevents sensitive account changes when a member also belongs to a company the caller does not own.

## Disclosure and references

- [Public GitHub Security Advisory](https://github.com/InvoiceShelf/InvoiceShelf/security/advisories/GHSA-c9cx-7r7m-264v)
- [VulDB submission #1028117](https://vuldb.com/submit/1028117)
- [InvoiceShelf repository](https://github.com/InvoiceShelf/InvoiceShelf)
- [Patch for the 2.x line, PR #826](https://github.com/InvoiceShelf/InvoiceShelf/pull/826)
- [Patch for the 3.x line, PR #822](https://github.com/InvoiceShelf/InvoiceShelf/pull/822)
- Audited commit: `0076ab9c5b1840d53690e721a1a4e7a91a068795`
- Public disclosure: 2026-09-23

## Credits

Research and disclosure credits requested for:

- Alysson Dutra
- Lucas Diniz
- [Fernando Viana](https://github.com/capivara-research)

The public GHSA currently lists `capivara-research` as Reporter and `gdarko` as Coordinator.

## Legal and ethical use

Use this material only on systems you own or have explicit permission to test. The reproducer is constrained to loopback laboratory targets. Do not test public or third-party InvoiceShelf installations.

