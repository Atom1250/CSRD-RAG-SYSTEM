import {
  validateFile,
  validateText,
  validateEmail,
  validateUrl,
  validatePath,
  validateSchemaType,
  validateQuery,
  formatFileSize,
} from '../validation';

// Mock File object for testing
class MockFile {
  name: string;
  size: number;
  type: string;

  constructor(name: string, size: number, type: string) {
    this.name = name;
    this.size = size;
    this.type = type;
  }
}

describe('Validation Utils', () => {
  describe('validateFile', () => {
    it('should validate a valid PDF file', () => {
      const file = new MockFile('test.pdf', 1024 * 1024, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject files that are too large', () => {
      const file = new MockFile('large.pdf', 100 * 1024 * 1024, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('exceeds maximum allowed size'))).toBe(true);
    });

    it('should reject files that are too small', () => {
      const file = new MockFile('tiny.pdf', 100, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('below minimum required size'))).toBe(true);
    });

    it('should reject unsupported file types', () => {
      const file = new MockFile('test.exe', 1024 * 1024, 'application/x-executable') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('not supported'))).toBe(true);
    });

    it('should reject files with invalid extensions', () => {
      const file = new MockFile('test.xyz', 1024 * 1024, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('extension'))).toBe(true);
    });

    it('should reject files with forbidden patterns in filename', () => {
      const file = new MockFile('../test.pdf', 1024 * 1024, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('invalid characters'))).toBe(true);
    });

    it('should reject empty filename', () => {
      const file = new MockFile('', 1024 * 1024, 'application/pdf') as File;
      const result = validateFile(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('File name cannot be empty');
    });
  });

  describe('validateText', () => {
    it('should validate normal text', () => {
      const result = validateText('Hello world');
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject text that is too short', () => {
      const result = validateText('Hi', { minLength: 5 });
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Minimum length is 5 characters');
    });

    it('should reject text that is too long', () => {
      const longText = 'a'.repeat(101);
      const result = validateText(longText, { maxLength: 100 });
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Maximum length is 100 characters');
    });

    it('should reject empty required text', () => {
      const result = validateText('', { required: true });
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('This field is required');
    });

    it('should validate text against pattern', () => {
      const result = validateText('abc123', { pattern: /^[a-z]+\d+$/ });
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject text that does not match pattern', () => {
      const result = validateText('ABC123', { 
        pattern: /^[a-z]+\d+$/, 
        patternMessage: 'Must be lowercase letters followed by numbers' 
      });
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Must be lowercase letters followed by numbers');
    });
  });

  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      const validEmails = [
        'test@example.com',
        'user.name@domain.co.uk',
        'user+tag@example.org'
      ];

      validEmails.forEach(email => {
        const result = validateEmail(email);
        expect(result.isValid).toBe(true);
      });
    });

    it('should reject invalid email addresses', () => {
      expect(validateEmail('invalid-email').isValid).toBe(false);
      expect(validateEmail('@example.com').isValid).toBe(false);
      expect(validateEmail('test@').isValid).toBe(false);
      expect(validateEmail('test@example').isValid).toBe(false);
      expect(validateEmail('test@.com').isValid).toBe(false);
      expect(validateEmail('test.@example.com').isValid).toBe(false);
    });
  });

  describe('validateUrl', () => {
    it('should validate correct URLs', () => {
      const validUrls = [
        'http://example.com',
        'https://www.example.com',
        'https://example.com/path?query=value#fragment'
      ];

      validUrls.forEach(url => {
        const result = validateUrl(url, true);
        expect(result.isValid).toBe(true);
      });
    });

    it('should reject invalid URLs', () => {
      const invalidUrls = [
        'not-a-url',
        'ftp://example.com',
        'example.com'
      ];

      invalidUrls.forEach(url => {
        const result = validateUrl(url, true);
        expect(result.isValid).toBe(false);
      });
    });

    it('should allow empty URL when not required', () => {
      const result = validateUrl('', false);
      expect(result.isValid).toBe(true);
    });
  });

  describe('validatePath', () => {
    it('should validate normal paths', () => {
      const validPaths = [
        '/home/user/documents',
        'C:\\Users\\Documents',
        './relative/path'
      ];

      validPaths.forEach(path => {
        const result = validatePath(path);
        expect(result.isValid).toBe(true);
      });
    });

    it('should reject paths with security issues', () => {
      const result = validatePath('/home/../etc/passwd');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('security reasons'))).toBe(true);
    });

    it('should reject paths that are too long', () => {
      const longPath = '/very/long/path/' + 'a'.repeat(500);
      const result = validatePath(longPath);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('Path is too long'))).toBe(true);
    });

    it('should reject paths with invalid characters', () => {
      const result = validatePath('/path/with<invalid>chars');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('invalid character'))).toBe(true);
    });

    it('should reject empty paths', () => {
      const result = validatePath('');
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Path is required');
    });
  });

  describe('validateSchemaType', () => {
    it('should validate correct schema types', () => {
      const validTypes = ['EU_ESRS_CSRD', 'UK_SRD', 'OTHER'];

      validTypes.forEach(type => {
        const result = validateSchemaType(type);
        expect(result.isValid).toBe(true);
      });
    });

    it('should reject invalid schema types', () => {
      const result = validateSchemaType('INVALID_TYPE');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(error => error.includes('Invalid schema type'))).toBe(true);
    });

    it('should reject empty schema type', () => {
      const result = validateSchemaType('');
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Schema type is required');
    });
  });

  describe('validateQuery', () => {
    it('should validate normal queries', () => {
      const result = validateQuery('What are the CSRD requirements?');
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject queries that are too short', () => {
      const result = validateQuery('Hi');
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Minimum length is 3 characters');
    });

    it('should reject queries that are too long', () => {
      const longQuery = 'a'.repeat(1001);
      const result = validateQuery(longQuery);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Maximum length is 1000 characters');
    });

    it('should reject empty queries', () => {
      const result = validateQuery('');
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('This field is required');
    });
  });

  describe('formatFileSize', () => {
    it('should format file sizes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1024 * 1024)).toBe('1 MB');
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
      expect(formatFileSize(1536)).toBe('1.50 KB');
    });
  });
});