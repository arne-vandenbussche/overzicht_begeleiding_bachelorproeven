BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "STUDENT" (
	"id"	INTEGER,
	"voornaam"	TEXT NOT NULL,
	"naam"	TEXT NOT NULL,
	"bedrijf"	TEXT,
	"aceproject"	TEXT,
	"opvolgingsdocument"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "OPVOLGING" (
	"id"	INTEGER,
	"datum"	TEXT NOT NULL,
	"type"	TEXT NOT NULL CHECK("type" IN ('contact', 'controle')),
	"omschrijving"	TEXT,
	"student"	INTEGER,
	PRIMARY KEY("id")
);
COMMIT;
