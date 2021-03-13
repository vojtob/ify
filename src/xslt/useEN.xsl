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
			<xsl:if test="property/@key = 'EN_name'">
				<!-- ak obsahuje atribut SK_name tak ho pouzi ako nove name -->
				<xsl:attribute name="name"> <!-- zmen hodnotu value -->
					<xsl:value-of select="property[@key = 'EN_name']/@value"/>
				</xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>