class GlossaryGenerator:
    @staticmethod
    def generate_glossary(concepts, relationships):
        """Build technical glossary entries with term definitions and related concepts."""
        # Create map of related concepts from relationships
        rel_map = {}
        for rel in relationships:
            src = rel['source']
            tgt = rel['target']
            
            if src not in rel_map:
                rel_map[src] = []
            if tgt not in rel_map:
                rel_map[tgt] = []
                
            if tgt not in rel_map[src]:
                rel_map[src].append(tgt)
            if src not in rel_map[tgt]:
                rel_map[tgt].append(src)

        glossary_items = []
        for concept in concepts:
            term_name = concept['name']
            related = rel_map.get(term_name, [])
            
            glossary_items.append({
                'document_id': concept.get('document_id'),
                'term': term_name,
                'definition': concept.get('definition', f"{term_name} is a key concept extracted from document text."),
                'frequency': concept.get('frequency', 1),
                'relevance_score': concept.get('relevance_score', 0.5),
                'category': concept.get('category', 'Technical Term'),
                'related_concepts': related[:6]  # top 6 related terms
            })

        # Sort alphabetically by default
        glossary_items.sort(key=lambda x: x['term'].lower())
        return glossary_items
