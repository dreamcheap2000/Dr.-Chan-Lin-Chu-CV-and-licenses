package com.phcep.service;

import com.phcep.model.SoapTemplate;
import com.phcep.repository.SoapTemplateRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class SoapTemplateService {

    private final SoapTemplateRepository soapTemplateRepository;

    /** All templates — frontend also filters by category client-side. */
    public List<SoapTemplate> listAll() {
        return soapTemplateRepository.findAllByOrderByCreatedAtAsc();
    }

    /** Templates filtered by category. */
    public List<SoapTemplate> listByCategory(String category) {
        return soapTemplateRepository.findByCategoryOrderByCreatedAtAsc(category);
    }

    public Optional<SoapTemplate> findById(UUID id) {
        return soapTemplateRepository.findById(id);
    }

    @Transactional
    public SoapTemplate create(SoapTemplate template) {
        return soapTemplateRepository.save(template);
    }

    @Transactional
    public SoapTemplate update(UUID id, SoapTemplate patch) {
        SoapTemplate existing = soapTemplateRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("SoapTemplate not found: " + id));
        if (patch.getName() != null) existing.setName(patch.getName());
        if (patch.getCategory() != null) existing.setCategory(patch.getCategory());
        if (patch.getContent() != null) existing.setContent(patch.getContent());
        return soapTemplateRepository.save(existing);
    }

    @Transactional
    public void delete(UUID id) {
        soapTemplateRepository.deleteById(id);
    }
}
