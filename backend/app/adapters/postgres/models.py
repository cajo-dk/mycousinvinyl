"""
SQLAlchemy models (database schema).

These are separate from domain entities to maintain clean architecture.
Each model includes to_domain() and from_domain() methods for conversion.
"""

from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Boolean, Date,
    ForeignKey, Table, CheckConstraint, UniqueConstraint, Enum as SQLEnum, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from app.adapters.postgres.database import Base
from app.domain import entities
from app.domain import value_objects as vo


# ============================================================================
# HELPERS
# ============================================================================

def _parse_active_years(active_years: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not active_years:
        return None, None
    value = active_years.strip()
    if not value:
        return None, None
    if "-" not in value:
        return value, None
    start, end = value.split("-", 1)
    start = start.strip() or None
    end = end.strip() or None
    return start, end


def _build_active_years(begin_date: Optional[str], end_date: Optional[str]) -> Optional[str]:
    start = (begin_date or "").strip()
    end = (end_date or "").strip()
    if not start and not end:
        return None
    if start and end:
        return f"{start}-{end}"
    if start:
        return f"{start}-"
    return f"-{end}"


# ============================================================================
# JUNCTION TABLES (Many-to-Many)
# ============================================================================

album_genres = Table(
    'album_genres',
    Base.metadata,
    Column('album_id', UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', UUID(as_uuid=True), ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

album_styles = Table(
    'album_styles',
    Base.metadata,
    Column('album_id', UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True),
    Column('style_id', UUID(as_uuid=True), ForeignKey('styles.id', ondelete='CASCADE'), primary_key=True)
)


# ============================================================================
# LOOKUP MODELS
# ============================================================================

class GenreModel(Base):
    """Genre lookup table."""
    __tablename__ = 'genres'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class StyleModel(Base):
    """Style lookup table."""
    __tablename__ = 'styles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    genre_id = Column(UUID(as_uuid=True), ForeignKey('genres.id', ondelete='SET NULL'), nullable=True)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CountryModel(Base):
    """Country lookup table."""
    __tablename__ = 'countries'

    code = Column(String(2), primary_key=True)  # ISO 3166-1 alpha-2
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ArtistTypeModel(Base):
    """Artist type lookup table."""
    __tablename__ = 'artist_types'

    code = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ReleaseTypeModel(Base):
    """Release type lookup table."""
    __tablename__ = 'release_types'

    code = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class EditionTypeModel(Base):
    """Edition type lookup table."""
    __tablename__ = 'edition_types'

    code = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class SleeveTypeModel(Base):
    """Sleeve type lookup table."""
    __tablename__ = 'sleeve_types'

    code = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# CORE ENTITY MODELS
# ============================================================================

class ArtistModel(Base):
    """Artist SQLAlchemy model."""
    __tablename__ = 'artists'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    sort_name = Column(String(255), nullable=False)
    type = Column(String(50), ForeignKey('artist_types.code', ondelete='RESTRICT'), nullable=False, default=vo.ArtistType.PERSON)
    country = Column(String(2), ForeignKey('countries.code', ondelete='SET NULL'), nullable=True)
    active_years = Column(String(50), nullable=True)
    disambiguation = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    aliases = Column(ARRAY(Text), nullable=True)
    notes = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    discogs_id = Column(Integer, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    data_source = Column(SQLEnum(vo.DataSource, name='data_source', values_callable=lambda x: [e.value for e in x]), default=vo.DataSource.USER)
    verification_status = Column(
        SQLEnum(vo.VerificationStatus, name='verification_status', values_callable=lambda x: [e.value for e in x]),
        default=vo.VerificationStatus.UNVERIFIED
    )

    def to_domain(self) -> entities.Artist:
        """Convert ORM model to domain entity."""
        begin_date, end_date = _parse_active_years(self.active_years)
        return entities.Artist(
            id=self.id,
            name=self.name,
            sort_name=self.sort_name,
            type=self.type,
            country=self.country,
            begin_date=begin_date,
            end_date=end_date,
            active_years=self.active_years,
            disambiguation=self.disambiguation,
            bio=self.bio,
            aliases=self.aliases or [],
            notes=self.notes,
            image_url=self.image_url,
            discogs_id=self.discogs_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            data_source=self.data_source,
            verification_status=self.verification_status,
            events=[]  # Events are cleared after conversion
        )

    @staticmethod
    def from_domain(entity: entities.Artist) -> 'ArtistModel':
        """Create ORM model from domain entity."""
        active_years = entity.active_years or _build_active_years(
            entity.begin_date, entity.end_date
        )
        return ArtistModel(
            id=entity.id,
            name=entity.name,
            sort_name=entity.sort_name,
            type=entity.type,
            country=entity.country,
            active_years=active_years,
            disambiguation=entity.disambiguation,
            bio=entity.bio,
            aliases=entity.aliases,
            notes=entity.notes,
            image_url=entity.image_url,
            discogs_id=entity.discogs_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            data_source=entity.data_source,
            verification_status=entity.verification_status
        )


class AlbumModel(Base):
    """Album SQLAlchemy model."""
    __tablename__ = 'albums'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    primary_artist_id = Column(UUID(as_uuid=True), ForeignKey('artists.id', ondelete='RESTRICT'), nullable=False)
    release_type = Column(String(50), ForeignKey('release_types.code', ondelete='RESTRICT'), nullable=False, default=vo.ReleaseType.STUDIO)
    original_release_year = Column(Integer, nullable=True)
    original_release_date = Column(Date, nullable=True)
    country_of_origin = Column(String(2), ForeignKey('countries.code', ondelete='SET NULL'), nullable=True)
    label = Column(String(255), nullable=True)
    catalog_number_base = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    original_release_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='SET NULL'), nullable=True)
    discogs_id = Column(Integer, nullable=True)

    # Full-text search
    search_vector = Column(TSVECTOR, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    data_source = Column(SQLEnum(vo.DataSource, name='data_source', values_callable=lambda x: [e.value for e in x]), default=vo.DataSource.USER)
    verification_status = Column(
        SQLEnum(vo.VerificationStatus, name='verification_status', values_callable=lambda x: [e.value for e in x]),
        default=vo.VerificationStatus.UNVERIFIED
    )

    # Relationships
    genres = relationship('GenreModel', secondary=album_genres, lazy='select')
    styles = relationship('StyleModel', secondary=album_styles, lazy='select')

    __table_args__ = (
        CheckConstraint('id != original_release_id', name='no_self_reference'),
    )

    def to_domain(self) -> entities.Album:
        """Convert ORM model to domain entity."""
        return entities.Album(
            id=self.id,
            title=self.title,
            primary_artist_id=self.primary_artist_id,
            release_type=self.release_type,
            original_release_year=self.original_release_year,
            original_release_date=self.original_release_date,
            country_of_origin=self.country_of_origin,
            label=self.label,
            catalog_number_base=self.catalog_number_base,
            description=self.description,
            image_url=self.image_url,
            original_release_id=self.original_release_id,
            discogs_id=self.discogs_id,
            genre_ids=[g.id for g in self.genres],
            style_ids=[s.id for s in self.styles],
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            data_source=self.data_source,
            verification_status=self.verification_status,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.Album) -> 'AlbumModel':
        """Create ORM model from domain entity."""
        return AlbumModel(
            id=entity.id,
            title=entity.title,
            primary_artist_id=entity.primary_artist_id,
            release_type=entity.release_type,
            original_release_year=entity.original_release_year,
            original_release_date=entity.original_release_date,
            country_of_origin=entity.country_of_origin,
            label=entity.label,
            catalog_number_base=entity.catalog_number_base,
            description=entity.description,
            image_url=entity.image_url,
            original_release_id=entity.original_release_id,
            discogs_id=entity.discogs_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            data_source=entity.data_source,
            verification_status=entity.verification_status
        )


class TrackModel(Base):
    """Track SQLAlchemy model."""
    __tablename__ = 'tracks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), nullable=False)
    side = Column(String(10), nullable=False)
    position = Column(String(10), nullable=False)
    title = Column(String(500), nullable=False)
    duration = Column(Integer, nullable=True)  # seconds
    songwriters = Column(ARRAY(Text), nullable=True)
    notes = Column(Text, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('album_id', 'side', 'position', name='uq_album_side_position'),
    )

    def to_domain(self) -> entities.Track:
        """Convert ORM model to domain entity."""
        return entities.Track(
            id=self.id,
            album_id=self.album_id,
            side=self.side,
            position=self.position,
            title=self.title,
            duration=self.duration,
            songwriters=self.songwriters or [],
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.Track) -> 'TrackModel':
        """Create ORM model from domain entity."""
        return TrackModel(
            id=entity.id,
            album_id=entity.album_id,
            side=entity.side,
            position=entity.position,
            title=entity.title,
            duration=entity.duration,
            songwriters=entity.songwriters,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class PressingModel(Base):
    """Pressing SQLAlchemy model."""
    __tablename__ = 'pressings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='RESTRICT'), nullable=False)
    format = Column(SQLEnum(vo.VinylFormat, name='vinyl_format', values_callable=lambda x: [e.value for e in x]), nullable=False)
    speed_rpm = Column(SQLEnum(vo.VinylSpeed, name='vinyl_speed', values_callable=lambda x: [e.value for e in x]), nullable=False)
    size_inches = Column(SQLEnum(vo.VinylSize, name='vinyl_size', values_callable=lambda x: [e.value for e in x]), nullable=False)
    disc_count = Column(Integer, nullable=False, default=1)
    pressing_country = Column(String(2), ForeignKey('countries.code', ondelete='SET NULL'), nullable=True)
    pressing_year = Column(Integer, nullable=True)
    pressing_plant = Column(String(255), nullable=True)
    mastering_engineer = Column(String(255), nullable=True)
    mastering_studio = Column(String(255), nullable=True)
    vinyl_color = Column(String(100), nullable=True)
    label_design = Column(String(255), nullable=True)
    image_url = Column(Text, nullable=True)
    edition_type = Column(String(50), ForeignKey('edition_types.code', ondelete='RESTRICT'), default=vo.EditionType.STANDARD)
    barcode = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    discogs_release_id = Column(Integer, nullable=True)
    discogs_master_id = Column(Integer, nullable=True)
    master_title = Column(String(500), nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    data_source = Column(SQLEnum(vo.DataSource, name='data_source', values_callable=lambda x: [e.value for e in x]), default=vo.DataSource.USER)
    verification_status = Column(
        SQLEnum(vo.VerificationStatus, name='verification_status', values_callable=lambda x: [e.value for e in x]),
        default=vo.VerificationStatus.UNVERIFIED
    )

    __table_args__ = (
        CheckConstraint('disc_count >= 1', name='chk_disc_count_positive'),
    )

    def to_domain(self) -> entities.Pressing:
        """Convert ORM model to domain entity."""
        return entities.Pressing(
            id=self.id,
            album_id=self.album_id,
            format=self.format,
            speed_rpm=self.speed_rpm,
            size_inches=self.size_inches,
            disc_count=self.disc_count,
            pressing_country=self.pressing_country,
            pressing_year=self.pressing_year,
            pressing_plant=self.pressing_plant,
            mastering_engineer=self.mastering_engineer,
            mastering_studio=self.mastering_studio,
            vinyl_color=self.vinyl_color,
            label_design=self.label_design,
            image_url=self.image_url,
            edition_type=self.edition_type,
            barcode=self.barcode,
            notes=self.notes,
            discogs_release_id=self.discogs_release_id,
            discogs_master_id=self.discogs_master_id,
            master_title=self.master_title,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            data_source=self.data_source,
            verification_status=self.verification_status,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.Pressing) -> 'PressingModel':
        """Create ORM model from domain entity."""
        return PressingModel(
            id=entity.id,
            album_id=entity.album_id,
            format=entity.format,
            speed_rpm=entity.speed_rpm,
            size_inches=entity.size_inches,
            disc_count=entity.disc_count,
            pressing_country=entity.pressing_country,
            pressing_year=entity.pressing_year,
            pressing_plant=entity.pressing_plant,
            mastering_engineer=entity.mastering_engineer,
            mastering_studio=entity.mastering_studio,
            vinyl_color=entity.vinyl_color,
            label_design=entity.label_design,
            image_url=entity.image_url,
            edition_type=entity.edition_type,
            barcode=entity.barcode,
            notes=entity.notes,
            discogs_release_id=entity.discogs_release_id,
            discogs_master_id=entity.discogs_master_id,
            master_title=entity.master_title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            data_source=entity.data_source,
            verification_status=entity.verification_status
        )


class MatrixModel(Base):
    """Matrix (runout code) SQLAlchemy model."""
    __tablename__ = 'matrices'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pressing_id = Column(UUID(as_uuid=True), ForeignKey('pressings.id', ondelete='CASCADE'), nullable=False)
    side = Column(String(10), nullable=False)
    matrix_code = Column(String(255), nullable=True)
    etchings = Column(Text, nullable=True)
    stamper_info = Column(String(255), nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('pressing_id', 'side', name='uq_pressing_side'),
    )

    def to_domain(self) -> entities.Matrix:
        """Convert ORM model to domain entity."""
        return entities.Matrix(
            id=self.id,
            pressing_id=self.pressing_id,
            side=self.side,
            matrix_code=self.matrix_code,
            etchings=self.etchings,
            stamper_info=self.stamper_info,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.Matrix) -> 'MatrixModel':
        """Create ORM model from domain entity."""
        return MatrixModel(
            id=entity.id,
            pressing_id=entity.pressing_id,
            side=entity.side,
            matrix_code=entity.matrix_code,
            etchings=entity.etchings,
            stamper_info=entity.stamper_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class PackagingModel(Base):
    """Packaging SQLAlchemy model."""
    __tablename__ = 'packaging'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pressing_id = Column(UUID(as_uuid=True), ForeignKey('pressings.id', ondelete='CASCADE'), nullable=False, unique=True)
    sleeve_type = Column(String(50), ForeignKey('sleeve_types.code', ondelete='RESTRICT'), nullable=False)
    cover_artist = Column(String(255), nullable=True)
    includes_inner_sleeve = Column(Boolean, default=False)
    includes_insert = Column(Boolean, default=False)
    includes_poster = Column(Boolean, default=False)
    includes_obi = Column(Boolean, default=False)
    stickers = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.Packaging:
        """Convert ORM model to domain entity."""
        return entities.Packaging(
            id=self.id,
            pressing_id=self.pressing_id,
            sleeve_type=self.sleeve_type,
            cover_artist=self.cover_artist,
            includes_inner_sleeve=self.includes_inner_sleeve,
            includes_insert=self.includes_insert,
            includes_poster=self.includes_poster,
            includes_obi=self.includes_obi,
            stickers=self.stickers,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.Packaging) -> 'PackagingModel':
        """Create ORM model from domain entity."""
        return PackagingModel(
            id=entity.id,
            pressing_id=entity.pressing_id,
            sleeve_type=entity.sleeve_type,
            cover_artist=entity.cover_artist,
            includes_inner_sleeve=entity.includes_inner_sleeve,
            includes_insert=entity.includes_insert,
            includes_poster=entity.includes_poster,
            includes_obi=entity.includes_obi,
            stickers=entity.stickers,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class CollectionItemModel(Base):
    """Collection item SQLAlchemy model."""
    __tablename__ = 'collection_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # References Azure AD user ID
    pressing_id = Column(UUID(as_uuid=True), ForeignKey('pressings.id', ondelete='RESTRICT'), nullable=False)
    media_condition = Column(SQLEnum(vo.Condition, name='condition_grade', values_callable=lambda x: [e.value for e in x]), nullable=False)
    sleeve_condition = Column(SQLEnum(vo.Condition, name='condition_grade', values_callable=lambda x: [e.value for e in x]), nullable=False)
    play_tested = Column(Boolean, default=False)
    defect_notes = Column(Text, nullable=True)
    purchase_price = Column(DECIMAL(10, 2), nullable=True)
    purchase_currency = Column(String(3), nullable=True)
    purchase_date = Column(Date, nullable=True)
    seller = Column(String(255), nullable=True)
    storage_location = Column(String(255), nullable=True)
    play_count = Column(Integer, default=0)
    last_played_date = Column(Date, nullable=True)
    user_rating = Column(Integer, nullable=True)
    user_notes = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('purchase_price >= 0', name='chk_purchase_price_positive'),
        CheckConstraint('play_count >= 0', name='chk_play_count_positive'),
        CheckConstraint('user_rating >= 0 AND user_rating <= 5', name='chk_user_rating_range'),
    )

    def to_domain(self) -> entities.CollectionItem:
        """Convert ORM model to domain entity."""
        return entities.CollectionItem(
            id=self.id,
            user_id=self.user_id,
            pressing_id=self.pressing_id,
            media_condition=self.media_condition,
            sleeve_condition=self.sleeve_condition,
            play_tested=self.play_tested,
            defect_notes=self.defect_notes,
            purchase_price=self.purchase_price,
            purchase_currency=self.purchase_currency,
            purchase_date=self.purchase_date,
            seller=self.seller,
            storage_location=self.storage_location,
            play_count=self.play_count,
            last_played_date=self.last_played_date,
            user_rating=self.user_rating,
            user_notes=self.user_notes,
            tags=self.tags or [],
            date_added=self.date_added,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.CollectionItem) -> 'CollectionItemModel':
        """Create ORM model from domain entity."""
        return CollectionItemModel(
            id=entity.id,
            user_id=entity.user_id,
            pressing_id=entity.pressing_id,
            media_condition=entity.media_condition,
            sleeve_condition=entity.sleeve_condition,
            play_tested=entity.play_tested,
            defect_notes=entity.defect_notes,
            purchase_price=entity.purchase_price,
            purchase_currency=entity.purchase_currency,
            purchase_date=entity.purchase_date,
            seller=entity.seller,
            storage_location=entity.storage_location,
            play_count=entity.play_count,
            last_played_date=entity.last_played_date,
            user_rating=entity.user_rating,
            user_notes=entity.user_notes,
            tags=entity.tags,
            date_added=entity.date_added,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class MediaAssetModel(Base):
    """Media asset SQLAlchemy model."""
    __tablename__ = 'media_assets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    media_type = Column(SQLEnum(vo.MediaType, name='media_type', values_callable=lambda x: [e.value for e in x]), nullable=False)
    url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by_user = Column(Boolean, default=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.MediaAsset:
        """Convert ORM model to domain entity."""
        return entities.MediaAsset(
            id=self.id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            media_type=self.media_type,
            url=self.url,
            description=self.description,
            uploaded_by_user=self.uploaded_by_user,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.MediaAsset) -> 'MediaAssetModel':
        """Create ORM model from domain entity."""
        return MediaAssetModel(
            id=entity.id,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            media_type=entity.media_type,
            url=entity.url,
            description=entity.description,
            uploaded_by_user=entity.uploaded_by_user,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class ExternalReferenceModel(Base):
    """External reference SQLAlchemy model."""
    __tablename__ = 'external_references'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    source = Column(SQLEnum(vo.ExternalSource, name='external_source', values_callable=lambda x: [e.value for e in x]), nullable=False)
    external_id = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'source', name='uq_entity_source'),
    )

    def to_domain(self) -> entities.ExternalReference:
        """Convert ORM model to domain entity."""
        return entities.ExternalReference(
            id=self.id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            source=self.source,
            external_id=self.external_id,
            url=self.url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.ExternalReference) -> 'ExternalReferenceModel':
        """Create ORM model from domain entity."""
        return ExternalReferenceModel(
            id=entity.id,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            source=entity.source,
            external_id=entity.external_id,
            url=entity.url,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class UserPreferencesModel(Base):
    """User preferences SQLAlchemy model."""
    __tablename__ = 'user_preferences'

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    currency = Column(String(3), nullable=False, default='DKK')
    display_settings = Column(JSONB, default={})

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.UserPreferences:
        """Convert ORM model to domain entity."""
        return entities.UserPreferences(
            user_id=self.user_id,
            currency=self.currency,
            display_settings=self.display_settings or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.UserPreferences) -> 'UserPreferencesModel':
        """Create ORM model from domain entity."""
        return UserPreferencesModel(
            user_id=entity.user_id,
            currency=entity.currency,
            display_settings=entity.display_settings,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class UserAlbumPlayModel(Base):
    """Per-user album play counts (overall)."""
    __tablename__ = 'user_album_plays'

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True)
    play_count = Column(Integer, nullable=False, default=0)
    last_played_at = Column(DateTime, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserAlbumPlayYearModel(Base):
    """Per-user album play counts by year."""
    __tablename__ = 'user_album_play_years'

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True)
    year = Column(Integer, primary_key=True)
    play_count = Column(Integer, nullable=False, default=0)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class DiscogsOAuthRequestModel(Base):
    """Discogs OAuth request token SQLAlchemy model."""
    __tablename__ = 'discogs_oauth_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    request_token = Column(Text, nullable=False, unique=True)
    request_secret = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    redirect_uri = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    def to_domain(self) -> entities.DiscogsOAuthRequest:
        return entities.DiscogsOAuthRequest(
            id=self.id,
            user_id=self.user_id,
            request_token=self.request_token,
            request_secret=self.request_secret,
            state=self.state,
            redirect_uri=self.redirect_uri,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )

    @staticmethod
    def from_domain(entity: entities.DiscogsOAuthRequest) -> 'DiscogsOAuthRequestModel':
        return DiscogsOAuthRequestModel(
            id=entity.id,
            user_id=entity.user_id,
            request_token=entity.request_token,
            request_secret=entity.request_secret,
            state=entity.state,
            redirect_uri=entity.redirect_uri,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
        )


class DiscogsUserTokenModel(Base):
    """Discogs OAuth access token SQLAlchemy model."""
    __tablename__ = 'discogs_user_tokens'

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    access_token = Column(Text, nullable=False)
    access_secret = Column(Text, nullable=True)
    discogs_username = Column(String(255), nullable=False)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.DiscogsUserToken:
        return entities.DiscogsUserToken(
            user_id=self.user_id,
            access_token=self.access_token,
            access_secret=self.access_secret,
            discogs_username=self.discogs_username,
            last_synced_at=self.last_synced_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(entity: entities.DiscogsUserToken) -> 'DiscogsUserTokenModel':
        return DiscogsUserTokenModel(
            user_id=entity.user_id,
            access_token=entity.access_token,
            access_secret=entity.access_secret,
            discogs_username=entity.discogs_username,
            last_synced_at=entity.last_synced_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class UserFollowsModel(Base):
    """User follows SQLAlchemy model for collection sharing."""
    __tablename__ = 'user_follows'

    follower_user_id = Column(UUID(as_uuid=True), primary_key=True)
    followed_user_id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('follower_user_id != followed_user_id', name='no_self_follow'),
    )


class MarketDataModel(Base):
    """Market data SQLAlchemy model."""
    __tablename__ = 'market_data'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pressing_id = Column(UUID(as_uuid=True), ForeignKey('pressings.id', ondelete='CASCADE'), nullable=False, unique=True)
    min_value = Column(DECIMAL(10, 2), nullable=True)
    median_value = Column(DECIMAL(10, 2), nullable=True)
    max_value = Column(DECIMAL(10, 2), nullable=True)
    last_sold_price = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), nullable=True)
    availability_status = Column(String(50), nullable=True)

    # System metadata
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.MarketData:
        """Convert ORM model to domain entity."""
        return entities.MarketData(
            id=self.id,
            pressing_id=self.pressing_id,
            min_value=self.min_value,
            median_value=self.median_value,
            max_value=self.max_value,
            last_sold_price=self.last_sold_price,
            currency=self.currency or 'DKK',
            availability_status=self.availability_status,
            updated_at=self.updated_at,
            events=[]
        )

    @staticmethod
    def from_domain(entity: entities.MarketData) -> 'MarketDataModel':
        """Create ORM model from domain entity."""
        return MarketDataModel(
            id=entity.id,
            pressing_id=entity.pressing_id,
            min_value=entity.min_value,
            median_value=entity.median_value,
            max_value=entity.max_value,
            last_sold_price=entity.last_sold_price,
            currency=entity.currency,
            availability_status=entity.availability_status,
            updated_at=entity.updated_at
        )


class CollectionImportModel(Base):
    """Collection import job SQLAlchemy model."""
    __tablename__ = 'collection_imports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default='queued')
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_summary = Column(Text, nullable=True)
    options = Column(JSONB, default={})

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self) -> entities.CollectionImport:
        """Convert ORM model to domain entity."""
        return entities.CollectionImport(
            id=self.id,
            user_id=self.user_id,
            filename=self.filename,
            status=self.status,
            total_rows=self.total_rows,
            processed_rows=self.processed_rows,
            success_count=self.success_count,
            error_count=self.error_count,
            started_at=self.started_at,
            completed_at=self.completed_at,
            error_summary=self.error_summary,
            options=self.options or {},
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @staticmethod
    def from_domain(entity: entities.CollectionImport) -> 'CollectionImportModel':
        """Create ORM model from domain entity."""
        return CollectionImportModel(
            id=entity.id,
            user_id=entity.user_id,
            filename=entity.filename,
            status=entity.status,
            total_rows=entity.total_rows,
            processed_rows=entity.processed_rows,
            success_count=entity.success_count,
            error_count=entity.error_count,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            error_summary=entity.error_summary,
            options=entity.options,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class CollectionImportRowModel(Base):
    """Collection import row SQLAlchemy model."""
    __tablename__ = 'collection_import_rows'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(UUID(as_uuid=True), ForeignKey('collection_imports.id', ondelete='CASCADE'), nullable=False)
    row_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default='pending')
    raw_data = Column(JSONB, default={})
    discogs_release_id = Column(Integer, nullable=True)
    artist_id = Column(UUID(as_uuid=True), ForeignKey('artists.id', ondelete='SET NULL'), nullable=True)
    album_id = Column(UUID(as_uuid=True), ForeignKey('albums.id', ondelete='SET NULL'), nullable=True)
    pressing_id = Column(UUID(as_uuid=True), ForeignKey('pressings.id', ondelete='SET NULL'), nullable=True)
    collection_item_id = Column(UUID(as_uuid=True), ForeignKey('collection_items.id', ondelete='SET NULL'), nullable=True)
    error_message = Column(Text, nullable=True)

    # System metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('import_id', 'row_number', name='uq_collection_import_row_number'),
    )

    def to_domain(self) -> entities.CollectionImportRow:
        """Convert ORM model to domain entity."""
        return entities.CollectionImportRow(
            id=self.id,
            import_id=self.import_id,
            row_number=self.row_number,
            status=self.status,
            raw_data=self.raw_data or {},
            discogs_release_id=self.discogs_release_id,
            artist_id=self.artist_id,
            album_id=self.album_id,
            pressing_id=self.pressing_id,
            collection_item_id=self.collection_item_id,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @staticmethod
    def from_domain(entity: entities.CollectionImportRow) -> 'CollectionImportRowModel':
        """Create ORM model from domain entity."""
        return CollectionImportRowModel(
            id=entity.id,
            import_id=entity.import_id,
            row_number=entity.row_number,
            status=entity.status,
            raw_data=entity.raw_data,
            discogs_release_id=entity.discogs_release_id,
            artist_id=entity.artist_id,
            album_id=entity.album_id,
            pressing_id=entity.pressing_id,
            collection_item_id=entity.collection_item_id,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class OutboxEventModel(Base):
    """Outbox event SQLAlchemy model for transactional outbox pattern."""
    __tablename__ = 'outbox_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    event_version = Column(String(20), nullable=False, default='1.0.0')
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    aggregate_type = Column(String(50), nullable=False)
    destination = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    headers = Column(JSONB, default={})
    event_metadata = Column('metadata', JSONB, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed = Column(Boolean, default=False)
