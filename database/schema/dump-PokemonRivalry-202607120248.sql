/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-12.3.2-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: PokemonRivalry
-- ------------------------------------------------------
-- Server version	10.11.15-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `Ability`
--

DROP TABLE IF EXISTS `Ability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Ability` (
  `AbilityID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(25) NOT NULL,
  `Description` mediumtext NOT NULL,
  PRIMARY KEY (`AbilityID`),
  UNIQUE KEY `AbilityID` (`AbilityID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lookup table for Pokémon abilities and their in-game descriptions';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Ability_pokemon`
--

DROP TABLE IF EXISTS `Ability_pokemon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Ability_pokemon` (
  `PokemonID` int(10) unsigned NOT NULL,
  `AbilityID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`PokemonID`,`AbilityID`),
  KEY `AbilityID` (`AbilityID`),
  CONSTRAINT `Ability_pokemon_ibfk_1` FOREIGN KEY (`AbilityID`) REFERENCES `Ability` (`AbilityID`) ON UPDATE CASCADE,
  CONSTRAINT `Ability_pokemon_ibfk_2` FOREIGN KEY (`PokemonID`) REFERENCES `Pokemon` (`PokemonID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Defines the pool of possible abilities for each species, including hidden abilities';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Item`
--

DROP TABLE IF EXISTS `Item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Item` (
  `ItemID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(20) NOT NULL,
  `Description` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ItemID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lookup table for held items';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Move`
--

DROP TABLE IF EXISTS `Move`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Move` (
  `MoveID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `TypeID` int(10) unsigned NOT NULL,
  `Name` varchar(20) NOT NULL,
  `Category` varchar(10) NOT NULL COMMENT 'Damage class: ''Physical'', ''Special'', or ''Status''',
  `PP` tinyint(3) unsigned NOT NULL,
  `Power` smallint(5) unsigned DEFAULT NULL COMMENT 'Base power of the move. NULL for non-damaging moves',
  `Accuracy` smallint(5) unsigned DEFAULT NULL COMMENT 'Accuracy percentage. NULL for moves that never miss',
  `Effect` mediumtext NOT NULL COMMENT 'Description of the movement',
  PRIMARY KEY (`MoveID`),
  UNIQUE KEY `Name` (`Name`),
  KEY `TypeID` (`TypeID`),
  CONSTRAINT `Move_ibfk_1` FOREIGN KEY (`TypeID`) REFERENCES `Type` (`TypeID`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lookup table for all battle moves, including power, accuracy, and priority';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Move_pokemon`
--

DROP TABLE IF EXISTS `Move_pokemon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Move_pokemon` (
  `PokemonID` int(10) unsigned NOT NULL,
  `MoveID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`PokemonID`,`MoveID`),
  KEY `MoveID` (`MoveID`),
  CONSTRAINT `Move_pokemon_ibfk_1` FOREIGN KEY (`MoveID`) REFERENCES `Move` (`MoveID`) ON UPDATE CASCADE,
  CONSTRAINT `Move_pokemon_ibfk_2` FOREIGN KEY (`PokemonID`) REFERENCES `Pokemon` (`PokemonID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Nature`
--

DROP TABLE IF EXISTS `Nature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Nature` (
  `NatureID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(10) NOT NULL,
  `StatChanged` varchar(15) NOT NULL COMMENT 'What stat changes in format (-St1, +St2) or nothing if the nature dosen''t change nothing',
  PRIMARY KEY (`NatureID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Pokemon`
--

DROP TABLE IF EXISTS `Pokemon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Pokemon` (
  `PokemonID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(20) NOT NULL,
  `Hp` smallint(6) NOT NULL,
  `Attack` smallint(6) NOT NULL,
  `Defense` smallint(6) NOT NULL,
  `SpAtk` smallint(6) NOT NULL,
  `SpDef` smallint(6) NOT NULL,
  `Speed` smallint(6) NOT NULL,
  `FrontSpriteGIF` varchar(255) NOT NULL COMMENT 'Relative path to the animated front sprite (GIF)',
  `BackSpriteGIF` varchar(255) NOT NULL COMMENT 'Relative path to the animated back sprite (GIF)',
  `FrontSpritePNG` varchar(255) NOT NULL COMMENT 'Relative path to the front sprite (PNG)',
  `BackSpritePNG` varchar(255) NOT NULL COMMENT 'Relative path to the back sprite (PNG)',
  PRIMARY KEY (`PokemonID`),
  UNIQUE KEY `PokemonID` (`PokemonID`),
  UNIQUE KEY `Name` (`Name`),
  UNIQUE KEY `FrontSprite` (`FrontSpriteGIF`),
  UNIQUE KEY `BackSprite` (`BackSpriteGIF`),
  UNIQUE KEY `Pokemon_UNIQUE` (`FrontSpritePNG`),
  UNIQUE KEY `Pokemon_UNIQUE_1` (`BackSpritePNG`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Basic stats and name for pokemon';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Team`
--

DROP TABLE IF EXISTS `Team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Team` (
  `TeamID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `UserID` int(10) unsigned NOT NULL,
  `Name` varchar(50) NOT NULL,
  `IsActive` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Indicates which of the user''s teams is currently active for battles.',
  `ActiveFlag` tinyint(4) GENERATED ALWAYS AS (case when `IsActive` = 1 then 1 else NULL end) VIRTUAL,
  PRIMARY KEY (`TeamID`),
  UNIQUE KEY `idx_unique_active_team` (`UserID`,`ActiveFlag`),
  CONSTRAINT `Team_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A named collection of up to 6 Pokémon owned by a specific user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Team_member`
--

DROP TABLE IF EXISTS `Team_member`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Team_member` (
  `TeamID` int(10) unsigned NOT NULL,
  `Slot` tinyint(3) unsigned NOT NULL,
  `PokemonID` int(10) unsigned NOT NULL,
  `NatureID` int(10) unsigned NOT NULL,
  `ItemID` int(10) unsigned DEFAULT NULL,
  `AbilityID` int(10) unsigned NOT NULL,
  `HpEVs` tinyint(3) unsigned NOT NULL,
  `AttackEVs` tinyint(3) unsigned NOT NULL,
  `DefenseEVs` tinyint(3) unsigned NOT NULL,
  `SpAtkEVs` tinyint(3) unsigned NOT NULL,
  `SpDefEVs` tinyint(3) unsigned NOT NULL,
  `SpeedEVs` tinyint(3) unsigned NOT NULL,
  `Move1ID` int(10) unsigned DEFAULT NULL,
  `Move2ID` int(10) unsigned DEFAULT NULL,
  `Move3ID` int(10) unsigned DEFAULT NULL,
  `Move4ID` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`TeamID`,`Slot`),
  KEY `ItemID` (`ItemID`),
  KEY `NatureID` (`NatureID`),
  KEY `PokemonID` (`PokemonID`,`AbilityID`),
  KEY `PokemonID_2` (`PokemonID`,`Move1ID`),
  KEY `PokemonID_3` (`PokemonID`,`Move2ID`),
  KEY `PokemonID_4` (`PokemonID`,`Move3ID`),
  KEY `PokemonID_5` (`PokemonID`,`Move4ID`),
  CONSTRAINT `Team_member_ibfk_1` FOREIGN KEY (`TeamID`) REFERENCES `Team` (`TeamID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_2` FOREIGN KEY (`ItemID`) REFERENCES `Item` (`ItemID`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_3` FOREIGN KEY (`PokemonID`) REFERENCES `Pokemon` (`PokemonID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_4` FOREIGN KEY (`NatureID`) REFERENCES `Nature` (`NatureID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_5` FOREIGN KEY (`PokemonID`, `AbilityID`) REFERENCES `Ability_pokemon` (`PokemonID`, `AbilityID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_6` FOREIGN KEY (`PokemonID`, `Move1ID`) REFERENCES `Move_pokemon` (`PokemonID`, `MoveID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_7` FOREIGN KEY (`PokemonID`, `Move2ID`) REFERENCES `Move_pokemon` (`PokemonID`, `MoveID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_8` FOREIGN KEY (`PokemonID`, `Move3ID`) REFERENCES `Move_pokemon` (`PokemonID`, `MoveID`) ON UPDATE CASCADE,
  CONSTRAINT `Team_member_ibfk_9` FOREIGN KEY (`PokemonID`, `Move4ID`) REFERENCES `Move_pokemon` (`PokemonID`, `MoveID`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Individual Pokémon instance within a team, including EVs, chosen ability, held item, and 4 moves';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Type`
--

DROP TABLE IF EXISTS `Type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Type` (
  `TypeID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(10) NOT NULL,
  PRIMARY KEY (`TypeID`),
  UNIQUE KEY `TypeID` (`TypeID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lookup table for the 18 elemental types';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Type_pokemon`
--

DROP TABLE IF EXISTS `Type_pokemon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Type_pokemon` (
  `PokemonID` int(10) unsigned NOT NULL,
  `TypeID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`PokemonID`,`TypeID`),
  KEY `TypeID` (`TypeID`),
  CONSTRAINT `Type_pokemon_ibfk_1` FOREIGN KEY (`PokemonID`) REFERENCES `Pokemon` (`PokemonID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `Type_pokemon_ibfk_2` FOREIGN KEY (`TypeID`) REFERENCES `Type` (`TypeID`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Junction table to handle Pokémon with up to two types';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `User` (
  `UserID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(20) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `Score` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'Player''s current battle ranking',
  PRIMARY KEY (`UserID`),
  UNIQUE KEY `Name` (`Name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'PokemonRivalry'
--

--
-- Dumping routines for database 'PokemonRivalry'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-07-12  2:48:37
