## Project rules
- Preserve published Git history. Make changes with new commits rather than force-pushing or rewriting existing commits.
- Squash PRs into main using a title that describes the changes and no commit-list body. Do not import automatic branch-sync commits into main.
- Each page is a complete HTML file. Keep its header, content, forms, and footer together in reading order.
- Use ordinary HTML and descriptive CSS class names. Do not reintroduce React components, templates, or generated page fragments.
- Shared styles live in styles.css. Shared interaction code lives in site.js. Keep visible copy and markup in the HTML files.
- Product pages live in vitrine/<product-id>/index.html. Product cards contain their filter and sort data as HTML data attributes. Keep these attributes consistent with each product page.
- The cart uses the existing cozy-manchot-cart localStorage key and id/size/qty format. Forms and checkout are demonstrations with no backend.
- Product visuals are inline SVG patterns. The brand forbids photography.
- Run npm run check, npm test, and npm run build before publishing source changes.
