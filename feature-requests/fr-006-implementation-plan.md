# FR-006 Implementation Plan
## Correcting Pressing/Discogs Master Relationship

**Feature Request ID:** FR-006
**Date:** 2025-12-25
**Status:** Planning

---

## Executive Summary

This feature request corrects the relationship between Pressings and Discogs Master Releases by:
1. Removing the internal `master_id` foreign key (which incorrectly modeled masters as pressings)
2. Adding `master_title` field to store the Discogs master release title
3. Implementing UI to search and select Discogs releases when creating pressings
4. Grouping pressings by master title in the Pressings view
5. Adding pagination at Artist, Album, and Pressing levels

---

## Current State Analysis

### Database Schema
**File:** `infrastructure/postgres/init.sql` (lines 177-208)

**Current fields:**
- ✅ `discogs_release_id INT` - Links to Discogs release
- ✅ `discogs_master_id INT` - Links to Discogs master
- ❌ `master_id UUID` - **REMOVE** (incorrect FK to another pressing)
- ❌ Missing `master_title VARCHAR(500)` - **ADD**

**Current constraints:**
- ❌ `chk_pressing_master_not_self` - **REMOVE**

### Backend Entity
**File:** `backend/app/domain/entities.py` (lines 384-444)

**Current Pressing entity:**
- ✅ Has `discogs_release_id: Optional[int]`
- ✅ Has `discogs_master_id: Optional[int]`
- ❌ Has `master_id: Optional[UUID]` - **REMOVE**
- ❌ Missing `master_title: Optional[str]` - **ADD**
- ❌ Validation for `master_id` (lines 440-441) - **REMOVE**

### Backend API Schemas
**File:** `backend/app/entrypoints/http/schemas/pressing.py`

**PressingBase (line 84-107):**
- Line 106: `master_id: Optional[UUID]` - **REMOVE**
- **ADD:** `master_title: Optional[str]`

**PressingUpdate (line 117-138):**
- Line 138: `master_id: Optional[UUID]` - **REMOVE**
- **ADD:** `master_title: Optional[str]`

**PressingDetailResponse (line 201-228):**
- Line 222: `master_id: Optional[UUID]` - **REMOVE**
- **ADD:** `master_title: Optional[str]`

### Frontend
**File:** `frontend/src/pages/Pressings.tsx`

**Current grouping structure:**
- Artist → Album → Pressing (lines 102-147)
- **NEEDS:** Artist → Album → Master Title → Pressing

**Missing features:**
- Discogs release search button in PressingForm
- Master title grouping in Pressings view
- Pagination at all levels

### Discogs Integration
**Files:**
- `backend/app/entrypoints/http/routers/discogs.py`
- `backend/app/entrypoints/http/schemas/discogs.py`

**Existing endpoint:**
- ✅ `/masters/{master_id}/releases` - Gets releases for a master (line 107-125)
- ✅ `/releases/{release_id}` - Gets release details (line 128-144)

**DiscogsReleaseSearchResult (line 59-69):**
- ✅ Has `master_id: Optional[int]`
- ❌ Missing `master_title: Optional[str]` - **ADD**

**DiscogsReleaseDetails (line 76-95):**
- ✅ Has `master_id: Optional[int]`
- ❌ Missing `master_title: Optional[str]` - **ADD**

---

## Implementation Plan

### Phase 1: Database Migration

**Task 1.1: Create Migration Script**
- **File:** `infrastructure/postgres/migrations/001_fr006_master_title.sql` (NEW)
- **Actions:**
  1. Add `master_title VARCHAR(500)` column to `pressings` table
  2. Drop `chk_pressing_master_not_self` constraint
  3. Drop `master_id` column (CASCADE to remove FK)

**Task 1.2: Update init.sql**
- **File:** `infrastructure/postgres/init.sql`
- **Changes:**
  - Line 197: Remove `master_id UUID REFERENCES pressings(id) ON DELETE SET NULL,`
  - Line 197: Add `master_title VARCHAR(500),`
  - Line 207: Remove `CONSTRAINT chk_pressing_master_not_self CHECK (master_id IS NULL OR master_id != id)`

**Estimated Effort:** 1 hour

---

### Phase 2: Backend Data Model Updates

**Task 2.1: Update Pressing Entity**
- **File:** `backend/app/domain/entities.py`
- **Changes:**
  - Line 412: Remove `master_id: Optional[UUID] = None`
  - Line 412: Add `master_title: Optional[str] = None`
  - Lines 440-441: Remove master_id validation
- **Estimated Effort:** 30 minutes

**Task 2.2: Update Pressing Schemas**
- **File:** `backend/app/entrypoints/http/schemas/pressing.py`
- **Changes:**
  - PressingBase (line 106): Replace `master_id` with `master_title: Optional[str] = Field(None, max_length=500)`
  - PressingUpdate (line 138): Replace `master_id` with `master_title: Optional[str] = Field(None, max_length=500)`
  - PressingDetailResponse (line 222): Replace `master_id` with `master_title: Optional[str] = None`
- **Estimated Effort:** 30 minutes

**Task 2.3: Update Pressing Repository**
- **File:** `backend/app/adapters/postgres/pressing_repository_adapter.py`
- **Changes:**
  - Update SQLAlchemy mappings to include `master_title` field
  - Remove `master_id` field mappings
- **Estimated Effort:** 30 minutes

**Task 2.4: Update Tests**
- **Files:** `backend/tests/unit/test_pressing.py`, `backend/tests/integration/test_pressing_*.py`
- **Changes:**
  - Remove tests for `master_id` validation
  - Add tests for `master_title` field
- **Estimated Effort:** 1 hour

---

### Phase 3: Discogs Integration Enhancement

**Task 3.1: Update Discogs Schemas**
- **File:** `backend/app/entrypoints/http/schemas/discogs.py`
- **Changes:**
  - DiscogsReleaseSearchResult (line 67): Add `master_title: Optional[str] = None`
  - DiscogsReleaseDetails (line 89): Add `master_title: Optional[str] = None`
- **Estimated Effort:** 15 minutes

**Task 3.2: Update Discogs Port**
- **File:** `backend/app/application/ports/discogs_client.py`
- **Changes:**
  - Update DiscogsReleaseSearchResult dataclass to include `master_title`
  - Update DiscogsReleaseDetails dataclass to include `master_title`
- **Estimated Effort:** 15 minutes

**Task 3.3: Update Discogs Client Adapter**
- **File:** `backend/app/adapters/http/discogs_client.py`
- **Changes:**
  - When fetching releases, also fetch master title if `master_id` is present
  - May require additional API call to get master details: `/masters/{master_id}`
  - Cache master titles to avoid redundant API calls
- **Estimated Effort:** 2 hours

**Task 3.4: New Endpoint - Search Releases for Album**
- **File:** `backend/app/entrypoints/http/routers/discogs.py`
- **New Endpoint:** `GET /discogs/albums/{album_id}/releases`
  - Takes album_id (internal UUID or Discogs ID - clarify which)
  - If internal UUID: Look up album's discogs_id
  - Search Discogs for releases by album's discogs_id
  - Return releases with master_title populated
  - Group results by master_id/master_title on frontend
- **Estimated Effort:** 2 hours

**Alternative Approach:**
- **New Endpoint:** `GET /discogs/albums/{discogs_album_id}/releases` (use Discogs ID directly)
  - Frontend passes album's discogs_id
  - Search Discogs for all releases associated with this album/master
  - Return releases grouped by master

---

### Phase 4: Frontend API Types

**Task 4.1: Update Frontend Types**
- **File:** `frontend/src/types/api.ts`
- **Changes:**
  - PressingCreate (line 447-468): Remove `master_id`, add `master_title?: string`
  - PressingUpdate (line 470-489): Remove `master_id`, add `master_title?: string`
  - PressingResponse (line 491-520): Remove `master_id`, add `master_title?: string`
  - PressingDetailResponse (line 535-559): Remove `master_id`, add `master_title?: string`
  - DiscogsReleaseSearchResult (line 183-194): Add `master_title?: string`
  - DiscogsReleaseDetails (line 200-220): Add `master_title?: string`
- **Estimated Effort:** 30 minutes

**Task 4.2: Update API Service**
- **File:** `frontend/src/api/services.ts` (or wherever Discogs API calls are defined)
- **Changes:**
  - Add method to search releases for an album
  - Add method to get release details
- **Estimated Effort:** 30 minutes

---

### Phase 5: Frontend - Pressing Form Enhancement (Story #1)

**Task 5.1: Create DiscogsReleaseSearchModal Component**
- **File:** `frontend/src/components/Modals/DiscogsReleaseSearchModal.tsx` (NEW)
- **Features:**
  - Triggered from PressingForm when "Search Discogs" button clicked
  - Calls API to get releases for album's discogs_id
  - Groups releases by `master_title`
  - Displays grouped list with expand/collapse
  - Each master group shows:
    - Master title (header)
    - List of releases under that master
  - Each release shows: year, country, label, format
  - Cannot select master itself (filter out `type === "master"`)
  - On selection, returns DiscogsReleaseDetails to parent
- **Estimated Effort:** 4 hours

**Task 5.2: Update PressingForm Component**
- **File:** `frontend/src/components/Forms/PressingForm.tsx`
- **Changes:**
  1. Add "Search Discogs Releases" button next to album field
  2. Button enabled only if album has `discogs_id`
  3. On click, open DiscogsReleaseSearchModal
  4. When release selected from modal:
     - Fill form fields from DiscogsReleaseDetails
     - Set `discogs_release_id` = selected release id
     - Set `discogs_master_id` = selected release's master_id
     - Set `master_title` = selected release's master_title
     - Fill other fields: country, year, label, format, barcode, etc.
  5. Remove any UI for `master_id` field
- **Estimated Effort:** 3 hours

---

### Phase 6: Frontend - Pressings View Enhancement (Story #2 & #3)

**Task 6.1: Update Pressings Page Grouping**
- **File:** `frontend/src/pages/Pressings.tsx`
- **Changes:**
  1. Update grouping logic (lines 102-147):
     - Current: Artist → Album → Pressing
     - New: Artist → Album → MasterTitle → Pressing
  2. Add `MasterGroup` interface:
     ```typescript
     interface MasterGroup {
       masterTitle: string;  // Use "Unknown Master" if null
       masterDiscogId: number | undefined;
       pressings: PressingDetailResponse[];
     }
     ```
  3. Update `AlbumGroup` to have `masters: MasterGroup[]` instead of `pressings`
  4. Group pressings by master_title within each album
- **Estimated Effort:** 2 hours

**Task 6.2: Add Multi-Level Pagination**
- **File:** `frontend/src/pages/Pressings.tsx`
- **Changes:**
  1. **Artist-level pagination** (currently exists - lines 190-194)
     - Keep existing logic
  2. **Album-level pagination** (NEW)
     - Add state: `artistAlbumPages: Record<string, number>` (current page per artist)
     - Add controls to paginate albums within each artist
     - Show X albums per artist (configurable, default 5)
  3. **Pressing-level pagination** (currently exists - lines 46)
     - Rename `albumPressingPages` to `masterPressingPages`
     - Change to track pressing page per master: `Record<string, number>`
     - Show Y pressings per master (configurable, default 10)
- **Estimated Effort:** 3 hours

**Task 6.3: Update Pressings View UI**
- **File:** `frontend/src/pages/Pressings.tsx` and `frontend/src/pages/Pressings.css`
- **Changes:**
  1. Update render structure to show 4-level hierarchy:
     ```
     Artist (expandable)
       → Album (expandable, paginated)
         → Master Title (expandable, paginated)
           → Pressing (list)
     ```
  2. Add expand/collapse icons for master groups
  3. Add pagination controls for albums and masters
  4. Style master title headers distinctly
  5. Show master Discogs ID if available
- **Estimated Effort:** 3 hours

---

### Phase 7: Testing & Documentation

**Task 7.1: Backend Integration Tests**
- Test pressing creation with master_title
- Test pressing update with master_title
- Test Discogs release search returns master_title
- Test pagination at all levels
- **Estimated Effort:** 2 hours

**Task 7.2: Frontend Integration Tests**
- Test DiscogsReleaseSearchModal grouping
- Test PressingForm auto-fill from Discogs
- Test Pressings view 4-level grouping
- Test pagination at all levels
- **Estimated Effort:** 2 hours

**Task 7.3: Update Documentation**
- Update docs/data-model.md with new pressing fields
- Update docs/reference-architecture.md if needed
- Add screenshots/examples to FR-006.md
- **Estimated Effort:** 1 hour

---

## Risk Assessment

### High Risk
1. **Data Migration**: Removing `master_id` FK could fail if there are existing references
   - **Mitigation**: Check for and clean up any existing master_id references before migration
   - **Fallback**: Keep master_id column but mark as deprecated if removal fails

2. **Discogs API Rate Limiting**: Fetching master titles for each release may hit rate limits
   - **Mitigation**: Implement caching of master titles
   - **Mitigation**: Batch fetch master details where possible

### Medium Risk
1. **Complex Frontend Grouping**: 4-level hierarchy with pagination is complex
   - **Mitigation**: Thorough testing with various data sets
   - **Mitigation**: Implement step-by-step, test each level

2. **Performance**: Grouping and pagination logic could be slow with large datasets
   - **Mitigation**: Profile and optimize grouping logic
   - **Mitigation**: Consider server-side grouping if needed

### Low Risk
1. **UI/UX Confusion**: Users may not understand master vs release concept
   - **Mitigation**: Add tooltip explaining Discogs masters
   - **Mitigation**: Show clear visual hierarchy

---

## Dependencies

### External
- Discogs API availability
- Discogs API rate limits

### Internal
- Database migration capability
- Backend API changes must be deployed before frontend

---

## Rollout Strategy

### Phase A: Backend-Only (Safe)
1. Deploy database migration
2. Deploy backend changes (master_title field support)
3. Verify existing functionality still works
4. **No frontend changes yet**

### Phase B: Pressing Form Enhancement
1. Deploy PressingForm changes (Discogs search)
2. Users can start using master_title field
3. **Pressings view still shows old grouping**

### Phase C: Pressings View Enhancement
1. Deploy Pressings view changes (master grouping + pagination)
2. Full feature available

---

## Effort Estimate Summary

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Phase 1: Database Migration | 2 tasks | 1.5 hours |
| Phase 2: Backend Data Model | 4 tasks | 2.5 hours |
| Phase 3: Discogs Integration | 4 tasks | 4.5 hours |
| Phase 4: Frontend API Types | 2 tasks | 1 hour |
| Phase 5: Pressing Form | 2 tasks | 7 hours |
| Phase 6: Pressings View | 3 tasks | 8 hours |
| Phase 7: Testing & Docs | 3 tasks | 5 hours |
| **TOTAL** | **20 tasks** | **29.5 hours** (~4 days) |

---

## Open Questions

1. **Album Release Search**:
   - Should the endpoint search by internal album UUID or Discogs album ID?
   - If by UUID: Need to verify album has discogs_id set
   - **Recommendation**: Use Discogs album ID directly for cleaner separation

2. **Master Title Storage**:
   - Store master title only, or also store master_discogs_id separately?
   - **Current plan**: We already have `discogs_master_id`, just adding `master_title`
   - ✅ **Resolved**: Store both fields

3. **Handling Releases Without Masters**:
   - Some releases might not have a master_id
   - **Recommendation**: Group under "Unknown Master" or "Standalone Releases"

4. **Default Pagination Values**:
   - How many items per page at each level?
   - **Recommendation**:
     - Artists: 10 per page (existing)
     - Albums per artist: 5 (show all if ≤5)
     - Masters per album: Show all (usually small)
     - Pressings per master: 10 per page

5. **Discogs Master API Calls**:
   - How to efficiently get master titles for many releases?
   - **Options**:
     - A) Call `/masters/{id}` for each unique master_id (could be slow)
     - B) Use Discogs microservice to batch fetch and cache
   - **Recommendation**: Implement caching in Discogs microservice

---

## Success Criteria

1. ✅ Database no longer has `master_id` FK to pressings table
2. ✅ Database has `master_title` field populated for pressings from Discogs
3. ✅ Users can search Discogs releases when creating a pressing
4. ✅ Discogs releases are grouped by master title in search modal
5. ✅ Pressing form auto-fills from selected Discogs release
6. ✅ Pressings view groups by: Artist → Album → Master Title → Pressing
7. ✅ Pagination works at Artist, Album, and Pressing levels
8. ✅ All existing tests pass
9. ✅ New tests cover master_title functionality
10. ✅ Documentation updated

---

## Next Steps

1. **Review and approve this plan** with stakeholders
2. **Answer open questions** (see section above)
3. **Create tickets** for each task in project management system
4. **Begin Phase 1** (Database Migration)
5. **Deploy phases incrementally** following rollout strategy
