<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	xmlns:archimate="http://www.archimatetool.com/archimate">

	<xsl:output method="xml" indent="yes"/>

	<xsl:template match="@* | node()">
		<xsl:copy>
			<xsl:apply-templates select="@* | node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="element[@name and (@xsi:type != 'archimate:ArchimateDiagramModel')]">
		<xsl:copy><!-- skopiruj element a zatial nic viac -->
			<xsl:apply-templates select="@*"/> <!-- skopiruj atributy elementu -->
			<xsl:choose>
				<xsl:when test="property/@key = 'EN_name'">
				</xsl:when>
				<xsl:otherwise>
					<xsl:element name="property">
						<xsl:attribute name="key">EN_name</xsl:attribute>
						<xsl:attribute name="value">
							<xsl:value-of select="@name"/>
						</xsl:attribute>
					</xsl:element>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="element/property[@key='EN_name']">
		<xsl:copy><!-- skopiruj element a zatial nic viac -->
			<xsl:apply-templates select="@*"/> <!-- skopiruj atributy elementu -->
			<xsl:attribute name="value"> <!-- zmen hodnotu value -->
				<xsl:value-of select="../@name"/>
			</xsl:attribute>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>