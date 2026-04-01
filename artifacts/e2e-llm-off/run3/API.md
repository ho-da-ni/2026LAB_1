# API Overview
- Endpoint Count: `2`
- Generated At: `2026-04-01T00:00:00Z`

## Metadata
- schema_version: `1.0.0`
- source: `ir_merged.json`
- base/head/merge_base: `main` / `work` / `UNKNOWN`

## Endpoint Index
| endpoint_id | method | path | handler | auth | feature_id |
|---|---|---|---|---|---|
| ep_0f5ab1b677c021ac | POST | /orders | com.acme.order.OrderController#create(OrderCreateRequest) | UNKNOWN | UNKNOWN |
| ep_8a96a6db7e77db48 | GET | /user/list.do | egov.sample.user.UserController#listUsers(HttpServletRequest) | UNKNOWN | UNKNOWN |

## Endpoints
### POST /orders (`ep_0f5ab1b677c021ac`)

#### Summary
- Handler: `com.acme.order.OrderController#create(OrderCreateRequest)`
- Feature: `UNKNOWN`
- Status: `unknown`

#### Request
- Content-Type: `UNKNOWN`
- Path Params: `UNKNOWN`
- Query Params: `UNKNOWN`
- Headers: `UNKNOWN`
- Body Schema: `UNKNOWN`

#### Response
- Success: `UNKNOWN`
- Error: `UNKNOWN`
- Response Schema: `UNKNOWN`

#### Security
- Auth Required: `UNKNOWN`
- Roles/Scopes: `UNKNOWN`

#### Exceptions
- `UNKNOWN`

#### Source Evidence
- File: `src/main/java/com/acme/order/OrderController.java`
- Symbol: `OrderController#create`
- Lines: `L42-L88`
- Annotation/Signature: `@PostMapping(path="/orders")`

#### needs_review
- 없음

### GET /user/list.do (`ep_8a96a6db7e77db48`)

#### Summary
- Handler: `egov.sample.user.UserController#listUsers(HttpServletRequest)`
- Feature: `UNKNOWN`
- Status: `unknown`

#### Request
- Content-Type: `UNKNOWN`
- Path Params: `UNKNOWN`
- Query Params: `UNKNOWN`
- Headers: `UNKNOWN`
- Body Schema: `UNKNOWN`

#### Response
- Success: `UNKNOWN`
- Error: `UNKNOWN`
- Response Schema: `UNKNOWN`

#### Security
- Auth Required: `UNKNOWN`
- Roles/Scopes: `UNKNOWN`

#### Exceptions
- `UNKNOWN`

#### Source Evidence
- File: `src/main/java/egov/sample/user/UserController.java`
- Symbol: `UserController#listUsers`
- Lines: `L31-L54`
- Annotation/Signature: `@RequestMapping(value="/user/list.do", method=RequestMethod.GET)`

#### needs_review
- 없음

## needs_review
| code | endpoint_id/target | detail |
|---|---|---|
| needs_review.mapping_route_conflict | /orders/{id} | 동일 METHOD+PATH에 handler 2개가 충돌하여 자동 병합 중단 |

## Appendix: Source Evidence Summary
- 본 문서는 `ir_merged.json` 기준 자동 생성되었다.
